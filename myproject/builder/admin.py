from django.contrib import admin
from .models import CategoryName
from .models import LessonVersion
from .models import LessonUpdateControl

admin.site.register(CategoryName)

@admin.register(LessonVersion)
class LessonVersionAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'version', 'updated_at', 'updated_by', 'comment')
    list_filter = ('lesson', 'updated_by')
    search_fields = ('lesson__title', 'title', 'comment')

@admin.register(LessonUpdateControl)
class LessonUpdateControlAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'version_number', 'update_date', 'next_update_date', 'responsible_role', 'responsible_fio')
    list_filter = ('lesson', 'responsible_role')
    search_fields = ('lesson__title', 'responsible_fio', 'comment')
