from django.contrib import admin
from django import forms
from .models import Course, Lesson, UserLessonTrajectory, Trajectory, TrajectoryCourse, UserCourseTrajectory

class UserLessonTrajectoryLessonInline(admin.TabularInline):
    model = UserLessonTrajectory.lessons.through
    extra = 1
    verbose_name = "Урок в траектории пользователя"
    verbose_name_plural = "Уроки в траектории пользователя"
    autocomplete_fields = ['lesson']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            # Фильтруем уроки по курсу траектории
            formset.form.base_fields['lesson'].queryset = Lesson.objects.filter(courses=obj.course)
        return formset

class LessonInline(admin.TabularInline):
    model = Lesson.courses.through
    extra = 1
    verbose_name = "Урок в курсе"
    verbose_name_plural = "Уроки в курсе"
    autocomplete_fields = ['lesson']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'image', 'slug', 'final_quiz']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['final_quiz']  # Для удобного поиска тестов
    filter_horizontal = ('allowed_groups',)
    inlines = [LessonInline]



@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'get_courses', 'category']
    list_filter = ['category', 'courses']
    search_fields = ['title', 'courses__title']
    filter_horizontal = ['courses']
    
    def get_courses(self, obj):
        return ", ".join([course.title for course in obj.courses.all()])
    get_courses.short_description = 'Курсы'


class TrajectoryCourseInline(admin.TabularInline):
    model = TrajectoryCourse
    extra = 1
    autocomplete_fields = ['course']
    ordering = ['order']
    fields = ['course', 'order']
    verbose_name = "Курс в траектории"
    verbose_name_plural = "Курсы в траектории"

@admin.register(Trajectory)
class TrajectoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    filter_horizontal = ('groups',)
    inlines = [TrajectoryCourseInline]
    autocomplete_fields = ['groups']

@admin.register(UserCourseTrajectory)
class UserCourseTrajectoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'trajectory', 'current_course', 'completed', 'started_at')
    list_filter = ('trajectory', 'completed')
    search_fields = ('user__username', 'trajectory__name')
    autocomplete_fields = ['user', 'trajectory', 'current_course']

@admin.register(TrajectoryCourse)
class TrajectoryCourseAdmin(admin.ModelAdmin):
    list_display = ('trajectory', 'course', 'order')
    list_filter = ('trajectory',)
    search_fields = ('trajectory__name', 'course__title')
    autocomplete_fields = ['trajectory', 'course']





# from django.contrib import admin
# from django import forms
# from .models import Course, Lesson, UserLessonTrajectory
# from .forms import UserLessonTrajectoryForm




# class LessonInline(admin.TabularInline):
#     model = UserLessonTrajectory.lessons.through
#     extra = 1
#     verbose_name = "Урок в траектории"
#     verbose_name_plural = "Уроки в траектории"

@admin.register(UserLessonTrajectory)
class UserLessonTrajectoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'get_lessons_count')
    list_filter = ('course', 'user')
    search_fields = ('user__username', 'course__title')
    inlines = [UserLessonTrajectoryLessonInline]
    exclude = ('lessons',)
    autocomplete_fields = ['course']

    def get_lessons_count(self, obj):
        return obj.lessons.count()
    get_lessons_count.short_description = 'Кол-во уроков'