from django.contrib import admin
from .models import UserCourse, QuizResult, UserAnswer, ChangeLog

admin.site.site_header = "Kupryazha"
admin.site.site_title = "Администрирование сайта"
admin.site.index_title = "Панель управления"

@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    list_display = ('user', 'course',)
    list_filter = ('course',)
    search_fields = ('user__username', 'course__title')

@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ('version', 'release_date', 'type', 'title', 'is_public')
    list_filter = ('type', 'is_public')
    search_fields = ('title', 'description')
    date_hierarchy = 'release_date'

admin.site.register(QuizResult)
admin.site.register(UserAnswer)