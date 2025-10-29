from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import Delegation
from .forms import DelegationCreateForm, DelegationFilterForm


class DelegationDashboardView(LoginRequiredMixin, TemplateView):
    """Главная страница панели делегирования с вкладками"""
    template_name = 'delegation/delegation_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Автоматически завершаем истекшие делегирования
        now = timezone.now()
        expired_delegations = Delegation.objects.filter(
            status='active',
            end_datetime__lt=now
        )
        if expired_delegations.exists():
            expired_delegations.update(status='completed')
        
        # Получаем делегирования за последние 30 дней
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Исходящие делегирования (где пользователь - передающий)
        outgoing = Delegation.objects.filter(
            delegator=user,
            created_at__gte=cutoff_date
        ).select_related('delegate', 'delegator').order_by('-created_at')
        
        # Входящие делегирования (где пользователь - принимающий)
        incoming = Delegation.objects.filter(
            delegate=user,
            created_at__gte=cutoff_date
        ).select_related('delegate', 'delegator').order_by('-created_at')
        
        # Ожидающие подтверждения (для бейджа на вкладке)
        pending_count = incoming.filter(status='pending').count()
        
        # Для администраторов - все делегирования
        if user.is_superuser or user.is_staff:
            all_delegations = Delegation.objects.filter(
                created_at__gte=cutoff_date
            ).select_related('delegate', 'delegator').order_by('-created_at')
            context['all_delegations'] = all_delegations
            context['filter_form'] = DelegationFilterForm(self.request.GET)
        
        context['outgoing_delegations'] = outgoing
        context['incoming_delegations'] = incoming
        context['pending_count'] = pending_count
        context['form'] = DelegationCreateForm(delegator=user)
        
        return context


class DelegationCreateView(LoginRequiredMixin, CreateView):
    """View для создания нового делегирования"""
    model = Delegation
    form_class = DelegationCreateForm
    template_name = 'delegation/delegation_create.html'
    success_url = reverse_lazy('delegation:delegation_dashboard')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['delegator'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Сохраняем без коммита, чтобы установить дополнительные поля
        delegation = form.save(commit=False)
        delegation.delegator = self.request.user
        delegation.status = 'pending'
        delegation.save()
        
        messages.success(
            self.request, 
            f'Делегирование создано. Ожидает подтверждения от {delegation.delegate.get_full_name() or delegation.delegate.username}'
        )
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при создании делегирования. Проверьте введенные данные.')
        return super().form_invalid(form)


class DelegationConfirmView(LoginRequiredMixin, TemplateView):
    """View для подтверждения делегирования"""
    
    def post(self, request, pk):
        delegation = get_object_or_404(Delegation, pk=pk)
        
        # Проверка прав: только принимающий может подтвердить
        if delegation.delegate != request.user:
            messages.error(request, 'У вас нет прав для подтверждения этого делегирования')
            return redirect('delegation:delegation_dashboard')
        
        # Проверка статуса
        if delegation.status != 'pending':
            messages.warning(request, 'Это делегирование уже обработано')
            return redirect('delegation:delegation_dashboard')
        
        if delegation.confirm():
            messages.success(
                request, 
                f'Вы подтвердили делегирование от {delegation.delegator.get_full_name()}'
            )
        else:
            messages.error(request, 'Не удалось подтвердить делегирование')
        
        return redirect('delegation:delegation_dashboard')


class DelegationRejectView(LoginRequiredMixin, TemplateView):
    """View для отклонения делегирования"""
    
    def post(self, request, pk):
        delegation = get_object_or_404(Delegation, pk=pk)
        
        # Проверка прав: только принимающий может отклонить
        if delegation.delegate != request.user:
            messages.error(request, 'У вас нет прав для отклонения этого делегирования')
            return redirect('delegation:delegation_dashboard')
        
        # Проверка статуса
        if delegation.status != 'pending':
            messages.warning(request, 'Это делегирование уже обработано')
            return redirect('delegation:delegation_dashboard')
        
        if delegation.reject():
            messages.success(
                request, 
                f'Вы отклонили делегирование от {delegation.delegator.get_full_name()}'
            )
        else:
            messages.error(request, 'Не удалось отклонить делегирование')
        
        return redirect('delegation:delegation_dashboard')


class DelegationCancelView(LoginRequiredMixin, TemplateView):
    """View для отмены делегирования передающим"""
    
    def post(self, request, pk):
        delegation = get_object_or_404(Delegation, pk=pk)
        
        # Проверка прав: только передающий может отменить
        if delegation.delegator != request.user:
            messages.error(request, 'У вас нет прав для отмены этого делегирования')
            return redirect('delegation:delegation_dashboard')
        
        # Проверка статуса
        if delegation.status not in ['pending', 'active']:
            messages.warning(request, 'Это делегирование нельзя отменить')
            return redirect('delegation:delegation_dashboard')
        
        if delegation.cancel():
            messages.success(request, 'Делегирование отменено')
        else:
            messages.error(request, 'Не удалось отменить делегирование')
        
        return redirect('delegation:delegation_dashboard')


class AdminDelegationListView(LoginRequiredMixin, ListView):
    """View для администраторов - полный журнал делегирований"""
    model = Delegation
    template_name = 'delegation/admin_delegation_list.html'
    context_object_name = 'delegations'
    paginate_by = 50
    
    def dispatch(self, request, *args, **kwargs):
        # Проверка прав администратора
        if not (request.user.is_superuser or request.user.is_staff):
            messages.error(request, 'У вас нет прав для просмотра этой страницы')
            return redirect('delegation:delegation_dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Delegation.objects.all().select_related('delegate', 'delegator')
        
        # Применяем фильтры
        form = DelegationFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('delegator'):
                queryset = queryset.filter(delegator=form.cleaned_data['delegator'])
            
            if form.cleaned_data.get('delegate'):
                queryset = queryset.filter(delegate=form.cleaned_data['delegate'])
            
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(created_at__gte=form.cleaned_data['date_from'])
            
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(created_at__lte=form.cleaned_data['date_to'])
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = DelegationFilterForm(self.request.GET)
        return context
