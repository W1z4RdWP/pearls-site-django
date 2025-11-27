from django.contrib import admin
from .models import InternalProduct


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
