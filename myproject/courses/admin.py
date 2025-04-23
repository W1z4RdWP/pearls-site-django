from django.contrib import admin
from django import forms
from .models import Course, Lesson, UserLessonTrajectory

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'image', 'slug']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'course']

class UserLessonTrajectoryForm(forms.ModelForm):
    class Meta:
        model = UserLessonTrajectory
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        lessons = cleaned_data.get('lessons')

        if course and lessons:
            for lesson in lessons:
                if lesson.course != course:
                    raise forms.ValidationError(
                        f"Урок '{lesson.title}' не принадлежит выбранному курсу."
                    )
        return cleaned_data

# class LessonInline(admin.TabularInline):
#     model = UserLessonTrajectory.lessons.through
#     extra = 1
#     verbose_name = "Урок в траектории"
#     verbose_name_plural = "Уроки в траектории"

@admin.register(UserLessonTrajectory)
class UserLessonTrajectoryAdmin(admin.ModelAdmin):
    form = UserLessonTrajectoryForm
    list_display = ('user', 'course')
    list_filter = ('course', 'user')
    search_fields = ('user__username', 'course__title')
    # inlines = [LessonInline]
    # exclude = ('lessons',)
    
    # def get_lessons_count(self, obj):
    #     return obj.lessons.count()
    # get_lessons_count.short_description = 'Кол-во уроков'