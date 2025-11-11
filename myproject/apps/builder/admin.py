from django.contrib import admin
from .models import CategoryName, Document, Incident, LessonVersion, LessonCategoryMirror, DictionaryTerm, DictionarySection, LessonAllowedRole, AuditLog
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json



admin.site.register(CategoryName)

@admin.register(LessonVersion)
class LessonVersionAdmin(admin.ModelAdmin):
    """Админка версий уроков с фильтрами и поиском."""
    list_display = ('lesson', 'version', 'updated_at', 'updated_by', 'comment')
    list_filter = ('lesson', 'updated_by')
    search_fields = ('lesson__title', 'title', 'comment')


@admin.register(LessonCategoryMirror)
class LessonCategoryMirrorAdmin(admin.ModelAdmin):
    """Админка зеркал уроков по категориям."""
    list_display = ('lesson', 'category', 'order')
    list_filter = ('lesson', 'category')
    search_fields = ('lesson__title', 'category__name')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Админка документов базы знаний."""
    list_display = ('title', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title',)


admin.site.register(Incident)

admin.site.register(DictionaryTerm)

admin.site.register(DictionarySection)




@admin.register(LessonAllowedRole)
class LessonAllowedRoleAdmin(admin.ModelAdmin):
    """Админка разрешённых должностей для уроков."""
    list_display = ('lesson', 'role', 'responsible_fio', 'added_at')
    list_filter = ('lesson', 'role', 'added_at')
    search_fields = ('lesson__title', 'role__name')
    ordering = ('lesson__title', 'role__name')

# class DictionaryTermAdmin(admin.ModelAdmin):
#     list_display = ('term', 'author', 'order', 'created_at', 'updated_at')
#     search_fields = ('term', 'definition', 'author__username')
#     ordering = ('order', 'term')

#     def save_model(self, request, obj, form, change):
#         if not obj.pk:
#             obj.author = request.user
#         obj.save()


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Админка аудита изменений по объектам БЗ."""
    list_display = (
        'timestamp', 'user_display', 'action', 'model_name', 
        'object_name', 'changes_summary', 'ip_address'
    )
    list_filter = (
        'action', 'model_name', 'timestamp', 'user'
    )
    search_fields = (
        'object_name', 'user__username', 'user__first_name', 
        'user__last_name', 'comment', 'ip_address'
    )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    readonly_fields = (
        'timestamp', 'user', 'action', 'content_type', 'object_id',
        'object_name', 'model_name', 'ip_address', 'old_values',
        'new_values', 'extra_data', 'comment', 'formatted_old_values',
        'formatted_new_values', 'formatted_extra_data'
    )
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('timestamp', 'user', 'action', 'ip_address')
        }),
        ('Объект', {
            'fields': ('model_name', 'object_name', 'content_type', 'object_id')
        }),
        ('Изменения', {
            'fields': ('formatted_old_values', 'formatted_new_values'),
            'classes': ('collapse',)
        }),
        ('Дополнительные данные', {
            'fields': ('formatted_extra_data', 'comment'),
            'classes': ('collapse',)
        })
    )
    
    def user_display(self, obj):
        """Отображение пользователя с ссылкой"""
        if obj.user:
            user_name = obj.user.get_full_name() or obj.user.username
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:auth_user_change', args=[obj.user.pk]),
                user_name
            )
        return 'Система'
    user_display.short_description = 'Пользователь'
    
    def changes_summary(self, obj):
        """Краткое описание изменений"""
        summary = obj.get_changes_summary()
        if summary:
            return summary[:100] + '...' if len(summary) > 100 else summary
        return '-'
    changes_summary.short_description = 'Изменения'
    
    def formatted_old_values(self, obj):
        """Форматированный вывод старых значений"""
        if obj.old_values:
            return format_html('<pre>{}</pre>', 
                             json.dumps(obj.old_values, ensure_ascii=False, indent=2))
        return '-'
    formatted_old_values.short_description = 'Старые значения'
    
    def formatted_new_values(self, obj):
        """Форматированный вывод новых значений"""
        if obj.new_values:
            return format_html('<pre>{}</pre>', 
                             json.dumps(obj.new_values, ensure_ascii=False, indent=2))
        return '-'
    formatted_new_values.short_description = 'Новые значения'
    
    def formatted_extra_data(self, obj):
        """Форматированный вывод дополнительных данных"""
        if obj.extra_data:
            return format_html('<pre>{}</pre>', 
                             json.dumps(obj.extra_data, ensure_ascii=False, indent=2))
        return '-'
    formatted_extra_data.short_description = 'Дополнительные данные'
    
    def has_add_permission(self, request):
        """Запрещаем добавление записей через админку"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрещаем изменение записей через админку"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Разрешаем удаление только суперпользователям"""
        return request.user.is_superuser