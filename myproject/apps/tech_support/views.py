from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, View

from .forms import TicketCreateForm, TicketCommentForm, TicketStaffUpdateForm
from .models import Ticket, TicketStatus, TicketComment


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        return HttpResponseForbidden('Доступ запрещён')


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    template_name = 'tech_support/support_chat.html'
    form_class = TicketCreateForm

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


class TicketListEntryView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return redirect('tech_support:ticket_list_staff')
        return redirect('tech_support:ticket_list_my')


class TicketListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Ticket
    template_name = 'tech_support/ticket_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Ticket.objects.all().order_by('-created_at')
        # staff: показываем только незакреплённые или закреплённые за текущим
        return Ticket.objects.filter(assigned_to__in=[None, user]).order_by('-created_at')


class MyTicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tech_support/my_ticket_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        return Ticket.objects.filter(created_by=self.request.user).order_by('-created_at')


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tech_support/ticket_detail.html'
    context_object_name = 'ticket'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user
        # Доступ: автор тикета, суперюзер, staff если тикет свободен или закреплён за ним
        if user == self.object.created_by or user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if user.is_staff and (self.object.assigned_to is None or self.object.assigned_to == user):
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden('Доступ запрещён')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        ticket = context['ticket']
        context['is_staff_view'] = user.is_staff or user.is_superuser
        if context['is_staff_view']:
            context['comment_form'] = TicketCommentForm()
            context['update_form'] = TicketStaffUpdateForm(instance=ticket)
        context['comments'] = TicketComment.objects.filter(ticket=ticket).order_by('created_at')
        return context


class TakeTicketView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if ticket.assigned_to and ticket.assigned_to != request.user:
            messages.error(request, 'Тикет уже взят другим сотрудником')
            return redirect('tech_support:ticket_detail', pk=pk)
        ticket.assigned_to = request.user
        ticket.save(update_fields=['assigned_to'])
        messages.success(request, 'Тикет принят в работу')
        return redirect('tech_support:ticket_detail', pk=pk)


class CloseTicketView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        closed_status = TicketStatus.objects.filter(is_active=False).order_by('id').first()
        if closed_status is None:
            messages.error(request, 'Не найден статус для закрытия тикета')
            return redirect('tech_support:ticket_detail', pk=pk)
        ticket.status = closed_status
        ticket.assigned_to = ticket.assigned_to or request.user
        ticket.closed_at = ticket.closed_at or timezone.now()
        ticket.save(update_fields=['status', 'assigned_to', 'closed_at'])
        messages.success(request, 'Тикет закрыт')
        return redirect('tech_support:ticket_detail', pk=pk)


class AddCommentView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
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


class UpdateTicketView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        form = TicketStaffUpdateForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тикет обновлён')
        else:
            messages.error(request, 'Исправьте ошибки формы')
        return redirect('tech_support:ticket_detail', pk=pk)