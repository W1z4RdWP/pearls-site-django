from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, View
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from datetime import timedelta

from .forms import TicketCreateForm, TicketCommentForm, TicketStaffUpdateForm
from .models import Ticket, TicketStatus, TicketComment


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        return HttpResponseForbidden('Доступ запрещён')


class TicketCreateView(CreateView):
    model = Ticket
    template_name = 'tech_support/support_chat.html'
    form_class = TicketCreateForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ticket = form.save(commit=False)
        ticket.created_by = self.request.user
        default_status = TicketStatus.objects.order_by('id').first()
        if default_status is None:
            form.add_error(None, 'Не настроены статусы тикетов. Обратитесь к администратору.')
            return self.form_invalid(form)
        ticket.status = default_status
        ticket.save()
        messages.success(self.request, 'Тикет создан')
        return redirect('tech_support:ticket_detail', pk=ticket.pk)


class TicketListEntryView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return redirect('tech_support:ticket_list_staff')
        return redirect('tech_support:ticket_list_my')


class TicketListView(ListView):
    model = Ticket
    template_name = 'tech_support/ticket_list.html'
    context_object_name = 'tickets'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Ticket.objects.all().order_by('-created_at')
        # staff: показываем только незакреплённые или закреплённые за текущим
        return Ticket.objects.filter(assigned_to__in=[None, user]).order_by('-created_at')


class MyTicketListView(ListView):
    model = Ticket
    template_name = 'tech_support/my_ticket_list.html'
    context_object_name = 'tickets'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Ticket.objects.filter(created_by=self.request.user).order_by('-created_at')


class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'tech_support/ticket_detail.html'
    context_object_name = 'ticket'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        self.object = self.get_object()
        user = request.user
        # Доступ: автор тикета, суперюзер, staff если тикет свободен или закреплён за ним
        if user == self.object.created_by or user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if user.is_staff and (self.object.assigned_to is None or self.object.assigned_to == user):
            return super().dispatch(request, *args, **kwargs)
        return render(request, '403.html', status=403)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        ticket = context['ticket']
        is_staff_view = user.is_staff or user.is_superuser
        is_closed = bool(ticket.status and not ticket.status.is_active)
        can_comment = (is_staff_view or (user == ticket.created_by)) and not is_closed
        context['is_staff_view'] = is_staff_view
        context['is_closed'] = is_closed
        context['can_comment'] = can_comment
        if can_comment:
            context['comment_form'] = TicketCommentForm()
        if is_staff_view:
            context['update_form'] = TicketStaffUpdateForm(instance=ticket)
        context['comments'] = TicketComment.objects.filter(ticket=ticket).order_by('created_at')
        return context


class TicketReportsView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    Представление для отображения отчетов по тикетам.
    """
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        period = request.GET.get('period', 'month')
        if period == 'week':
            start_date = timezone.now() - timedelta(days=7)
        elif period == 'month':
            start_date = timezone.now() - timedelta(days=30)
        else:
            start_date = timezone.now() - timedelta(days=365)

        tickets_by_period = Ticket.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')

        performer_stats = Ticket.objects.filter(
            assigned_to__isnull=False,
            created_at__gte=start_date
        ).values(
            'assigned_to__username'
        ).annotate(
            total=Count('id'),
            resolved=Count('id', filter=Q(status__name='Решена')),
            avg_rating=Avg('rating')
        ).order_by('-total')

        resolved_tickets = Ticket.objects.filter(
            status__name='Решена',
            resolved_at__isnull=False,
            created_at__gte=start_date
        )

        avg_resolution_time = 0
        if resolved_tickets.exists():
            total_time = sum([
                (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                for ticket in resolved_tickets
            ])
            avg_resolution_time = total_time / resolved_tickets.count()

        context = {
            'period': period,
            'tickets_by_period': tickets_by_period,
            'performer_stats': performer_stats,
            'avg_resolution_time': round(avg_resolution_time, 1),
            'total_resolved': resolved_tickets.count(),
        }
        return render(request, 'tech_support/ticket_reports.html', context)



class StaffDashboardView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    Представление для отображения дашборда для сотрудников поддержки.
    """
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        total_tickets = Ticket.objects.count()
        active_tickets = Ticket.objects.filter(status__is_active=True).count()
        resolved_tickets = Ticket.objects.filter(status__name='Решена').count()
        overdue_tickets = Ticket.objects.filter(
            status__is_active=True,
            deadline__lt=timezone.now()
        ).count()

        priority_stats = Ticket.objects.filter(status__is_active=True).values(
            'priority__name'
        ).annotate(count=Count('id')).order_by('priority__level')

        type_stats = Ticket.objects.values('ticket_type').annotate(
            count=Count('id')
        ).order_by('-count')

        ticket_type_map = dict(Ticket.TICKET_TYPES)
        for stat in type_stats:
            stat['ticket_type_display'] = ticket_type_map.get(stat['ticket_type'], stat['ticket_type'])

        avg_rating = Ticket.objects.filter(rating__isnull=False).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0

        recent_tickets = Ticket.objects.order_by('-created_at')[:10]

        overdue_tickets_list = Ticket.objects.filter(
            status__is_active=True,
            deadline__lt=timezone.now()
        ).order_by('deadline')[:10]

        context = {
            'total_tickets': total_tickets,
            'active_tickets': active_tickets,
            'resolved_tickets': resolved_tickets,
            'overdue_tickets': overdue_tickets,
            'priority_stats': priority_stats,
            'type_stats': type_stats,
            'avg_rating': round(avg_rating, 1),
            'recent_tickets': recent_tickets,
            'overdue_tickets_list': overdue_tickets_list,
        }
        return render(request, 'tech_support/staff_dashboard.html', context)



class TakeTicketView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if ticket.status and not ticket.status.is_active:
            messages.error(request, 'Тикет закрыт, брать в работу нельзя')
            return redirect('tech_support:ticket_detail', pk=pk)
        if ticket.assigned_to and ticket.assigned_to != request.user:
            messages.error(request, 'Тикет уже взят другим сотрудником')
            return redirect('tech_support:ticket_detail', pk=pk)
        ticket.assigned_to = request.user
        update_fields = ['assigned_to']
        # Пытаемся установить статус "В работе" при взятии тикета
        in_progress_status = TicketStatus.objects.filter(name__iexact='В работе', is_active=True).first()
        if in_progress_status and ticket.status_id != in_progress_status.id:
            ticket.status = in_progress_status
            update_fields.append('status')
        ticket.save(update_fields=update_fields)
        messages.success(request, 'Тикет принят в работу')
        return redirect('tech_support:ticket_detail', pk=pk)


class CloseTicketView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        closed_status = TicketStatus.objects.filter(is_active=False).order_by('id').first()
        if closed_status is None:
            messages.error(request, 'Не найден статус для закрытия тикета')
            return redirect('tech_support:ticket_detail', pk=pk)
        ticket.status = closed_status
        ticket.assigned_to = ticket.assigned_to or request.user
        ticket.resolved_at = ticket.resolved_at or timezone.now()
        ticket.save(update_fields=['status', 'assigned_to', 'resolved_at'])
        messages.success(request, 'Тикет закрыт')
        return redirect('tech_support:ticket_detail', pk=pk)


class AddCommentView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        # Запрещаем комментировать закрытые тикеты
        if ticket.status and not ticket.status.is_active:
            return render(request, '403.html', status=403)
        # Разрешаем комментировать автору тикета и персоналу
        if not (request.user == ticket.created_by or request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            TicketComment.objects.create(
                ticket=ticket,
                author=request.user,
                content=form.cleaned_data['content'],
                is_internal=False
            )
            messages.success(request, 'Комментарий добавлен')
        else:
            messages.error(request, 'Ошибка валидации комментария')
        return redirect('tech_support:ticket_detail', pk=pk)


class UpdateTicketView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        form = TicketStaffUpdateForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тикет обновлён')
        else:
            messages.error(request, 'Исправьте ошибки формы')
        return redirect('tech_support:ticket_detail', pk=pk)


# Staff API: наличие новых тикетов (непринятых в работу)
@login_required
def new_tickets_count(request):
    user = request.user
    if not (user.is_staff or user.is_superuser):
        return JsonResponse({'detail': 'forbidden'}, status=403)
    count = Ticket.objects.filter(assigned_to__isnull=True, status__is_active=True).count()
    return JsonResponse({'count': count, 'has_new': count > 0})