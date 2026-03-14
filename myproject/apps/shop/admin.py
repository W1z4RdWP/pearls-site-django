from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import transaction
from .models import InternalProduct, ProductOrder


@admin.register(InternalProduct)
class InternalProductAdmin(admin.ModelAdmin):
    """Административная панель для управления товарами магазина"""
    
    list_display = [
        'id',
        'name',
        'points_price',
        'constraints',
        'is_active',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'constraints',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'description',
        'restrictions_text',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'points_price', 'image', 'is_active')
        }),
        ('Ограничения', {
            'fields': ('constraints', 'restrictions_text'),
            'description': 'Укажите частоту использования и подробное описание ограничений'
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        qs = super().get_queryset(request)
        return qs


@admin.register(ProductOrder)
class ProductOrderAdmin(admin.ModelAdmin):
    """Административная панель для управления заказами товаров"""
    
    list_display = [
        'id',
        'user_display',
        'product_display',
        'points_spent',
        'status_badge',
        'created_at',
        'reviewed_by_display',
    ]
    
    list_filter = [
        'status',
        'created_at',
        'reviewed_at',
    ]
    
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'product__name',
    ]
    
    readonly_fields = [
        'user',
        'product',
        'points_spent',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('user', 'product', 'points_spent', 'status'),
            'description': 'Внимание: При изменении статуса на "Отклонен" или "Отменен" баллы автоматически возвращаются пользователю.'
        }),
        ('Проверка администратором', {
            'fields': ('reviewed_by', 'reviewed_at', 'admin_comment')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    actions = ['approve_orders', 'reject_orders', 'cancel_orders', 'complete_orders']
    
    def user_display(self, obj):
        """Отображение пользователя с ссылкой"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.get_full_name() or obj.user.username
        )
    user_display.short_description = 'Пользователь'
    
    def product_display(self, obj):
        """Отображение товара"""
        return format_html(
            '<a href="/admin/shop/internalproduct/{}/change/">{}</a>',
            obj.product.id,
            obj.product.name
        )
    product_display.short_description = 'Товар'
    
    def status_badge(self, obj):
        """Отображение статуса с цветом"""
        colors = {
            'pending': 'warning',
            'approved': 'info',
            'rejected': 'danger',
            'completed': 'success',
            'cancelled': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def reviewed_by_display(self, obj):
        """Отображение администратора, проверившего заказ"""
        if obj.reviewed_by:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.reviewed_by.id,
                obj.reviewed_by.get_full_name() or obj.reviewed_by.username
            )
        return '-'
    reviewed_by_display.short_description = 'Проверил'
    
    def approve_orders(self, request, queryset):
        """Одобрить выбранные заказы"""
        updated = queryset.filter(status='pending').update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'Одобрено заказов: {updated}')
    approve_orders.short_description = 'Одобрить выбранные заказы'
    
    def reject_orders(self, request, queryset):
        """Отклонить выбранные заказы (баллы будут автоматически возвращены пользователю через сигналы)"""
        # Фильтруем только заказы, которые еще не отклонены/отменены
        orders_to_reject = queryset.exclude(status__in=['rejected', 'cancelled'])
        
        updated_count = 0
        
        with transaction.atomic():
            for order in orders_to_reject:
                # Обновляем статус (сигналы автоматически вернут баллы)
                order.status = 'rejected'
                order.reviewed_by = request.user
                order.reviewed_at = timezone.now()
                order.save()  # Сигналы сработают здесь и вернут баллы
                
                updated_count += 1
        
        self.message_user(
            request, 
            f'Отклонено заказов: {updated_count}. Баллы автоматически возвращены пользователям.',
            level='success'
        )
    reject_orders.short_description = 'Отклонить выбранные заказы (баллы вернутся автоматически)'
    
    def cancel_orders(self, request, queryset):
        """Отменить выбранные заказы (баллы будут автоматически возвращены пользователю через сигналы)"""
        # Отменяем только заказы, которые еще не отменены и не отклонены
        orders_to_cancel = queryset.exclude(status__in=['cancelled', 'rejected'])
        
        updated_count = 0
        
        with transaction.atomic():
            for order in orders_to_cancel:
                # Обновляем статус (сигналы автоматически вернут баллы)
                order.status = 'cancelled'
                order.reviewed_by = request.user
                order.reviewed_at = timezone.now()
                order.save()  # Сигналы сработают здесь и вернут баллы
                
                updated_count += 1
        
        self.message_user(
            request, 
            f'Отменено заказов: {updated_count}. Баллы автоматически возвращены пользователям.',
            level='success'
        )
    cancel_orders.short_description = 'Отменить выбранные заказы (баллы вернутся автоматически)'
    
    def complete_orders(self, request, queryset):
        """Завершить выбранные заказы"""
        updated = queryset.filter(status='approved').update(
            status='completed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'Завершено заказов: {updated}')
    complete_orders.short_description = 'Завершить выбранные заказы'
    
    def save_model(self, request, obj, form, change):
        """Автоматическое заполнение полей при сохранении"""
        if change and 'status' in form.changed_data:
            if obj.status in ['approved', 'rejected', 'completed'] and not obj.reviewed_by:
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
