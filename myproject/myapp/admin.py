from django.contrib import admin
from .models import UserCourse

admin.site.site_header = "Kupryazha"
admin.site.site_title = "Администрирование сайта"
admin.site.index_title = "Панель управления"

@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'start_date', 'is_completed')
    list_filter = ('course', 'is_completed')
    search_fields = ('user__username', 'course__title')
