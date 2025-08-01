from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'notification_type', 'title', 'message', 'is_read')
        }),
        ('Связанные объекты', {
            'fields': ('related_course', 'related_trajectory', 'related_lesson', 'points_change'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} уведомлений отмечено как прочитанные')
    mark_as_read.short_description = "Отметить как прочитанные"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} уведомлений отмечено как непрочитанные')
    mark_as_unread.short_description = "Отметить как непрочитанные"
