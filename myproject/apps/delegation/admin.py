from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Delegation


@admin.register(Delegation)
class DelegationAdmin(admin.ModelAdmin):
    """Административная панель для управления делегированиями"""
    
    list_display = [
        'id', 
        'delegator_display', 
        'delegate_display', 
        'delegated_permissions_short',
        'start_datetime',
        'end_datetime',
        'status_badge',
        'comment_display',
        'created_at',
        'is_active_now'
    ]
    
    list_filter = [
        'status',
        'comment',
        'created_at',
        'start_datetime',
        'end_datetime',
        'confirmed_by_assistant'
    ]
    
    search_fields = [
        'delegator__username',
        'delegator__first_name',
        'delegator__last_name',
        'delegate__username',
        'delegate__first_name',
        'delegate__last_name',
        'delegated_permissions'
    ]
    
    readonly_fields = [
        'created_at',
        'confirmed_at',
        'is_active_now'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('delegator', 'delegate', 'delegated_permissions')
        }),
        ('Период делегирования', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Статус и подтверждения', {
            'fields': ('status', 'confirmed_at', 'confirmed_by_assistant')
        }),
        ('Дополнительная информация', {
            'fields': ('comment', 'created_at')
        }),
    )
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    actions = ['mark_as_completed', 'mark_as_cancelled', 'confirm_by_assistant']
    
    def delegator_display(self, obj):
        """Отображение передающего"""
        return obj.delegator.get_full_name() or obj.delegator.username
    delegator_display.short_description = 'Передающий'
    
    def delegate_display(self, obj):
        """Отображение принимающего"""
        return obj.delegate.get_full_name() or obj.delegate.username
    delegate_display.short_description = 'Принимающий'
    
    def delegated_permissions_short(self, obj):
        """Краткое отображение прав"""
        if len(obj.delegated_permissions) > 50:
            return obj.delegated_permissions[:50] + '...'
        return obj.delegated_permissions
    delegated_permissions_short.short_description = 'Делегируемые права'
    
    def status_badge(self, obj):
        """Отображение статуса с цветовым бейджем"""
        colors = {
            'pending': '#ffc107',
            'active': '#28a745',
            'completed': '#6c757d',
            'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def comment_display(self, obj):
        """Отображение причины"""
        if obj.comment:
            return obj.get_comment_display()
        return '—'
    comment_display.short_description = 'Причина'
    
    def is_active_now(self, obj):
        """Проверка активности в текущий момент"""
        if obj.is_active():
            return format_html('<span style="color: green;">✓ Активно сейчас</span>')
        return format_html('<span style="color: gray;">✗ Не активно</span>')
    is_active_now.short_description = 'Активно сейчас'
    
    # Actions
    def mark_as_completed(self, request, queryset):
        """Массовое завершение делегирований"""
        updated = queryset.filter(status='active').update(status='completed')
        self.message_user(request, f'Завершено делегирований: {updated}')
    mark_as_completed.short_description = 'Завершить выбранные делегирования'
    
    def mark_as_cancelled(self, request, queryset):
        """Массовая отмена делегирований"""
        updated = queryset.filter(status__in=['pending', 'active']).update(status='cancelled')
        self.message_user(request, f'Отменено делегирований: {updated}')
    mark_as_cancelled.short_description = 'Отменить выбранные делегирования'
    
    def confirm_by_assistant(self, request, queryset):
        """Подтверждение бизнес-ассистентом"""
        updated = queryset.update(confirmed_by_assistant=True)
        self.message_user(request, f'Подтверждено делегирований: {updated}')
    confirm_by_assistant.short_description = 'Подтвердить выбранные (бизнес-ассистент)'
    
    def get_queryset(self, request):
        """Оптимизация запроса"""
        qs = super().get_queryset(request)
        return qs.select_related('delegator', 'delegate')
