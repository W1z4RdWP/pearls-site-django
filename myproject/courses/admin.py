from django.contrib import admin
from .models import Course, Lesson, UserLessonTrajectory
from myapp.models import UserCourse

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'image', 'slug']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'course']

admin.site.register(UserCourse)
admin.site.register(UserLessonTrajectory)