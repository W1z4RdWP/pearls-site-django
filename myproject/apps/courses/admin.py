from django.contrib import admin
from django import forms
from .models import Course, Lesson, UserLessonTrajectory, \
        Trajectory, TrajectoryCourse, UserCourseTrajectory, \
        Certificate, MetricsSubmission




class UserLessonTrajectoryLessonInline(admin.TabularInline):
    """Inline для редактирования уроков в `UserLessonTrajectory`."""
    model = UserLessonTrajectory.lessons.through
    extra = 1
    verbose_name = "Урок в траектории пользователя"
    verbose_name_plural = "Уроки в траектории пользователя"
    autocomplete_fields = ['lesson']


    def get_formset(self, request, obj=None, **kwargs):
        """Ограничивает выпадающий список уроков курсом траектории."""
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            # Фильтруем уроки по курсу траектории
            formset.form.base_fields['lesson'].queryset = Lesson.objects.filter(courses=obj.course)
        return formset




class LessonInline(admin.TabularInline):
    """Inline для связи `Lesson` в составе `Course`."""
    model = Lesson.courses.through
    extra = 1
    verbose_name = "Урок в курсе"
    verbose_name_plural = "Уроки в курсе"
    autocomplete_fields = ['lesson']




@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Админка модели `Course` c inline уроками и фильтрами."""
    list_display = ['title', 'description', 'image', 'slug', 'final_quiz']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['final_quiz']  # Для удобного поиска тестов
    filter_horizontal = ('allowed_groups',)
    inlines = [LessonInline]




@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Админка `Lesson` с отображением курсов и фильтрами."""
    list_display = ['title', 'order', 'required_time', 'get_courses', 'category']
    list_filter = ['category', 'courses']
    search_fields = ['title', 'courses__title']
    filter_horizontal = ['courses']
    exclude = ['video_id']
    

    def get_courses(self, obj):
        return ", ".join([course.title for course in obj.courses.all()])
    get_courses.short_description = 'Курсы'




class TrajectoryCourseInline(admin.TabularInline):
    """Inline для связи `Trajectory` и `Course` с полем порядка."""
    model = TrajectoryCourse
    extra = 1
    autocomplete_fields = ['course']
    ordering = ['order']
    fields = ['course', 'order']
    verbose_name = "Курс в траектории"
    verbose_name_plural = "Курсы в траектории"




@admin.register(Trajectory)
class TrajectoryAdmin(admin.ModelAdmin):
    """Админка `Trajectory` с inline курсов и группами."""
    list_display = ('name', 'description')
    search_fields = ('name',)
    filter_horizontal = ('groups',)
    inlines = [TrajectoryCourseInline]
    autocomplete_fields = ['groups']




@admin.register(UserCourseTrajectory)
class UserCourseTrajectoryAdmin(admin.ModelAdmin):
    """Админка индивидуальных траекторий пользователя."""
    list_display = ('user', 'trajectory', 'current_course', 'completed', 'started_at')
    list_filter = ('trajectory', 'completed')
    search_fields = ('user__username', 'trajectory__name')
    autocomplete_fields = ['user', 'trajectory', 'current_course']




@admin.register(TrajectoryCourse)
class TrajectoryCourseAdmin(admin.ModelAdmin):
    """Админка промежуточной модели `TrajectoryCourse`."""
    list_display = ('trajectory', 'course', 'order')
    list_filter = ('trajectory',)
    search_fields = ('trajectory__name', 'course__title')
    autocomplete_fields = ['trajectory', 'course']




@admin.register(UserLessonTrajectory)
class UserLessonTrajectoryAdmin(admin.ModelAdmin):
    """Админка `UserLessonTrajectory` с inline уроками."""
    list_display = ('user', 'course', 'get_lessons_count')
    list_filter = ('course', 'user')
    search_fields = ('user__username', 'course__title')
    inlines = [UserLessonTrajectoryLessonInline]
    exclude = ('lessons',)
    autocomplete_fields = ['course']


    def get_lessons_count(self, obj):
        return obj.lessons.count()
    get_lessons_count.short_description = 'Кол-во уроков'




@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Админка сертификатов (создаются автоматически, только просмотр)."""
    list_display = ('certificate_id', 'user', 'certificate_type', 'course', 'trajectory', 'issued_at')
    list_filter = ('certificate_type', 'issued_at')
    search_fields = ('user__username', 'certificate_id', 'course__title', 'trajectory__name')
    readonly_fields = ('certificate_id', 'issued_at')
    autocomplete_fields = ['user', 'course', 'trajectory']
    

    def has_add_permission(self, request):
        # Сертификаты создаются автоматически системой
        return False




@admin.register(MetricsSubmission)
class MetricsSubmissionAdmin(admin.ModelAdmin):
    """Админка отправленных форм метрик."""
    list_display = ('id', 'user', 'clinic_name', 'initial_month', 'doctors_count', 'chairs_count', 'submitted_at')
    list_filter = ('initial_month', 'submitted_at', 'doctors_count')
    search_fields = ('user__username', 'user__email', 'clinic_name')
    readonly_fields = ('submitted_at',)
    autocomplete_fields = ['user']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'clinic_name', 'submitted_at')
        }),
        ('Параметры клиники', {
            'fields': ('initial_month', 'doctors_count', 'chairs_count')
        }),
        ('График работы', {
            'fields': ('hours_weekdays', 'hours_saturday', 'hours_sunday')
        }),
        ('Рабочие дни по месяцам', {
            'fields': ('days_month_1', 'days_month_2', 'days_month_3', 
                      'days_month_4', 'days_month_5', 'days_month_6'),
            'classes': ('collapse',)
        }),
        ('Данные врачей и метрики', {
            'fields': ('doctors_data',),
            'classes': ('collapse',)
        }),
    )

    
    def get_queryset(self, request):
        """Оптимизирует запрос за счёт select_related."""
        return super().get_queryset(request).select_related('user')
    

    def has_add_permission(self, request):
        # Формы заполняются пользователями через сайт
        return False
