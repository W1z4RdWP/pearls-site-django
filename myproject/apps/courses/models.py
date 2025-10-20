from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone

from unidecode import unidecode

from quizzes.models import Quiz
from builder.models import CategoryName




class CourseManager(models.Manager):
    """Менеджер курса: выборки доступности/назначения для пользователя."""
    def available_for_user(self, user):
        """Все доступные курсы"""
        if user.is_staff or user.is_superuser:
            return self.all()
        
        # Получаем все курсы, доступные пользователю
        available_courses = self.filter(
            models.Q(usercourse__user=user) |
            models.Q(allowed_groups__in=user.groups.all()) |
            models.Q(trajectorycourse__trajectory__usercoursetrajectory__user=user)
        ).distinct()
        
        # Проверяем, нужно ли скрывать специализированные курсы
        if self._should_hide_specialized_courses(user):
            # Специализированные группы для медсестер/ассистентов
            specialized_groups = [
                "Медицинская сестра/ассистент в хирургии",
                "Медицинская сестра/ассистент в терапии", 
                "Медицинская сестра/ассистент в ортопедии",
                "Медицинская сестра/ассистент в ортодонтии"
            ]
            
            # Исключаем курсы, доступные только для специализированных групп
            user_specialized_groups = user.groups.filter(name__in=specialized_groups)
            if user_specialized_groups.exists():
                # Исключаем курсы, которые доступны только через специализированные группы
                # и не назначены пользователю напрямую
                specialized_courses = self.filter(
                    allowed_groups__in=user_specialized_groups
                ).exclude(
                    usercourse__user=user
                )
                
                available_courses = available_courses.exclude(
                    id__in=specialized_courses.values_list('id', flat=True)
                )
        
        return available_courses
    
    def _should_hide_specialized_courses(self, user):
        """
        Проверяет, нужно ли скрывать специализированные курсы для пользователя.
        Скрывает, если пользователь состоит в группе "Медсестра/ассистент" И в специализированной группе,
        но еще не завершил курс "Внедрение м/с и асс. День 6."
        """
        # Проверяем, состоит ли пользователь в группе "Медсестра/ассистент"
        nurse_assistant_group = user.groups.filter(name="Медсестра/ассистент").first()
        if not nurse_assistant_group:
            return False
        
        # Специализированные группы для медсестер/ассистентов
        specialized_groups = [
            "Медицинская сестра/ассистент в хирургии",
            "Медицинская сестра/ассистент в терапии", 
            "Медицинская сестра/ассистент в ортопедии",
            "Медицинская сестра/ассистент в ортодонтии"
        ]
        
        # Проверяем, состоит ли пользователь в какой-либо из специализированных групп
        user_specialized_groups = user.groups.filter(name__in=specialized_groups)
        if not user_specialized_groups.exists():
            return False
        
        # Проверяем, завершил ли пользователь курс "Внедрение м/с и асс. День 6."
        from myapp.models import UserCourse
        intro_course_completed = UserCourse.objects.filter(
            user=user,
            course__title__icontains="Внедрение м/с и асс. День 6",
            status='completed'
        ).exists()
        
        # Если курс не завершен, скрываем специализированные курсы
        return not intro_course_completed

    def accessible_via_trajectories(self, user):
        """Курсы, доступные только через траектории"""
        return self.filter(
            trajectorycourse__trajectory__usercoursetrajectory__user=user
        ).exclude(
            models.Q(usercourse__user=user) |
            models.Q(allowed_groups__in=user.groups.all())
        ).distinct()
    

    def accessible_via_groups(self, user):
        """Курсы, доступные только через группы"""
        courses = self.filter(
            allowed_groups__in=user.groups.all()
        ).exclude(
            models.Q(usercourse__user=user) |
            models.Q(trajectorycourse__trajectory__usercoursetrajectory__user=user)
        ).distinct()
        
        # Проверяем, нужно ли скрывать специализированные курсы
        if self._should_hide_specialized_courses(user):
            # Специализированные группы для медсестер/ассистентов
            specialized_groups = [
                "Медицинская сестра/ассистент в хирургии",
                "Медицинская сестра/ассистент в терапии", 
                "Медицинская сестра/ассистент в ортопедии",
                "Медицинская сестра/ассистент в ортодонтии"
            ]
            
            # Исключаем курсы, доступные только для специализированных групп
            user_specialized_groups = user.groups.filter(name__in=specialized_groups)
            if user_specialized_groups.exists():
                specialized_courses = self.filter(
                    allowed_groups__in=user_specialized_groups
                ).exclude(
                    usercourse__user=user
                )
                
                courses = courses.exclude(
                    id__in=specialized_courses.values_list('id', flat=True)
                )
        
        return courses
    

    def directly_assigned(self, user):
        """Курсы, напрямую назначенные пользователю"""
        return self.filter(usercourse__user=user).distinct()




class Course(models.Model):
    """
    Модель представляющая таблицу myapp_course с курсами.

    Attrs:
        title (CharField) - заголовок курса
        description (TextField) - описание курса
        allowed_groups (ManyToMany) - группы пользователей, которым автоматически назначентся выбранный курс.
        
    """
   
    title = models.CharField(max_length=200, verbose_name="Название курса")
    description = CKEditor5Field('Описание курса', config_name='noTablesImages', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    image = models.ImageField(upload_to='course_images/', default='course_images/default.jpg', blank=True, null=True, verbose_name="Изображение курса")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    final_quiz = models.ForeignKey(
        Quiz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Финальный тест"
    )
    allowed_groups = models.ManyToManyField(
        Group, 
        blank=True,
        verbose_name="Доступен для групп",
        help_text="Группы, которым доступен этот курс"
    )
    points = models.PositiveIntegerField(default=30, verbose_name="Количество DASCOIN за прохождение курса")
    certificate = models.BooleanField(default=False, verbose_name="Выдавать сертификат", help_text="Выдавать сертификат пользователю при завершении курса")
    objects = CourseManager()
    

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_course_per_author'
            )
        ]
        ordering = ['-created_at']


    @property
    def lessons(self):
        """Возвращает уроки курса через связь many-to-many, отсортированные по `order`."""
        return self.course_lessons.all().order_by('order')
    

    @property
    def quizzes(self):
        """Возвращает тесты курса через связь many-to-many, отсортированные по `order`, `name`."""
        return self.course_quizzes.all().order_by('order', 'name')
    

    def get_course_materials(self):
        """Собирает все материалы курса (уроки + тесты) в одну упорядоченную ленту."""
        materials = []
        
        # Добавляем уроки
        for lesson in self.lessons:
            materials.append({
                'type': 'lesson',
                'object': lesson,
                'order': lesson.order,
                'title': lesson.title,
                'id': lesson.id
            })
        
        # Добавляем тесты
        for quiz in self.quizzes:
            materials.append({
                'type': 'quiz',
                'object': quiz,
                'order': quiz.order,
                'title': quiz.name,
                'id': quiz.id
            })
        
        # Сортируем по порядку
        materials.sort(key=lambda x: x['order'])
        return materials

    @property
    def total_time_minutes(self):
        """Возвращает общее время курса в минутах (сумма времени всех уроков)."""
        return sum(lesson.required_time for lesson in self.lessons)

    @property
    def total_time_hours(self):
        """Возвращает общее время курса в часах (округлено до 1 знака после запятой)."""
        return round(self.total_time_minutes / 60, 1)

    def save(self, *args, **kwargs):
        """Автогенерирует уникальный `slug` при первом сохранении."""
        if not self.slug:  # Генерируем slug только если он пустой
            transliterated_slug = unidecode(self.title)
            self.slug = slugify(transliterated_slug, allow_unicode=True)
            # Проверяем уникальность slug
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

class Lesson(models.Model):
    """
    Класс отвечающий за таблицу уроков в БД.
    Attrs:
        title - название урока.
        content - содержимое урока. Заполняется администратором сайта.
        video_id - идентификатор прикрепленного видео из рутуб. Максимальное количество символов для передачи в форму 
                    задается параметром max_length.
    """

    title = models.CharField(max_length=200, verbose_name="Название урока")
    content = CKEditor5Field('Content', config_name='extends')
    video_id = models.CharField(
        max_length=100, 
        verbose_name="ID видео с Rutube (не используется)", 
        blank=True, 
        null=True,
        help_text="ПОЛЕ НЕ ИСПОЛЬЗУЕТСЯ"
    )
    order = models.PositiveIntegerField(verbose_name="Порядок урока")
    category = models.ForeignKey(
        CategoryName,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name="Категория"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    points = models.PositiveIntegerField(default=10, verbose_name="Количество DASCOIN за прохождение урока")
    required_time = models.PositiveIntegerField(default=7, verbose_name="Необходимое время (минуты)", help_text="Время в минутах, необходимое для прохождения урока")
    
    # Связь many-to-many с курсами для гибкости
    courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name='course_lessons',
        verbose_name="Выберите курсы, куда добавить урок"
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']
        indexes = [
            models.Index(fields=['order'], name='lesson_order_idx'),
        ]


    def get_previous_lesson(self, course=None):
        """Возвращает предыдущий урок относительно текущего `order` (в курсе или глобально)."""
        if course:
            # Если указан курс, ищем предыдущий урок в этом курсе
            return Lesson.objects.filter(
                courses=course, 
                order__lt=self.order
            ).order_by('-order').first()
        else:
            # Иначе ищем глобально по порядку
            return Lesson.objects.filter(
                order__lt=self.order
            ).order_by('-order').first()


    def get_next_lesson(self, course=None):
        """Возвращает следующий урок относительно текущего `order` (в курсе или глобально)."""
        if course:
            # Если указан курс, ищем следующий урок в этом курсе
            return Lesson.objects.filter(
                courses=course, 
                order__gt=self.order
            ).order_by('order').first()
        else:
            # Иначе ищем глобально по порядку
            return Lesson.objects.filter(
                order__gt=self.order
            ).order_by('order').first()


    def __str__(self):
        return self.title
    



class UserLessonTrajectory(models.Model):
    """
    Модель для хранения траектории прохождения курса для каждого пользователя.
    Связывает пользователя, курс и множество уроков, которые доступны этому пользователю.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Курс")
    lessons = models.ManyToManyField(Lesson, verbose_name="Уроки в траектории")


    class Meta:
        verbose_name = 'Траектория уроков пользователя'
        verbose_name_plural = 'Траектории уроков пользователей'
        unique_together = ('user', 'course')
        indexes = [
            models.Index(fields=['user', 'course'], name='ult_user_course_idx'),
        ]


    def __str__(self):
        return f"Траектория {self.user.username} для {self.course.title}"




class Trajectory(models.Model):
    """
    Траектория курсов. Может быть назначена нескольким группам и содержать курсы в определённом порядке.
    """

    name: str = models.CharField(max_length=255, verbose_name="Название траектории")
    description: str = models.TextField(blank=True, verbose_name="Описание")
    groups: models.ManyToManyField = models.ManyToManyField(
        Group,
        blank=True,
        verbose_name="Группы",
        help_text="Группы пользователей, которым назначается эта траектория"
    )
    courses: models.ManyToManyField = models.ManyToManyField(
        'Course',
        through='TrajectoryCourse',
        verbose_name="Курсы в траектории"
    )
    points = models.PositiveIntegerField(default=100, verbose_name="Количество DASCOIN за прохождение траектории")
    certificate = models.BooleanField(default=False, verbose_name="Выдавать сертификат", help_text="Выдавать сертификат пользователю при завершении траектории")


    class Meta:
        verbose_name = 'Траектория курсов'
        verbose_name_plural = 'Траектории курсов'
        ordering = ['name']


    def __str__(self) -> str:
        return self.name




class TrajectoryCourse(models.Model):
    """
    Промежуточная модель для связи Trajectory и Course с порядком (order).
    """

    trajectory: Trajectory = models.ForeignKey(Trajectory, on_delete=models.CASCADE)
    course: Course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order: int = models.PositiveIntegerField(verbose_name="Порядок курса в траектории")


    class Meta:
        unique_together = ('trajectory', 'course')
        ordering = ['order']
        verbose_name = 'Курс в траектории'
        verbose_name_plural = 'Курсы в траектории'
        indexes = [
            models.Index(fields=['trajectory', 'order'], name='tc_trajectory_order_idx'),
        ]


    def __str__(self) -> str:
        return f"{self.trajectory.name}: {self.course.title} (#{self.order})"


class UserCourseTrajectory(models.Model):
    """
    Индивидуальная траектория пользователя: к какой Trajectory он привязан, и прогресс по курсам.
    """

    user: User = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    trajectory: Trajectory = models.ForeignKey(Trajectory, on_delete=models.CASCADE, verbose_name="Траектория")
    current_course: Course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Текущий курс")
    started_at: timezone.datetime = models.DateTimeField(auto_now_add=True, verbose_name="Дата назначения")
    completed: bool = models.BooleanField(default=False, verbose_name="Завершена ли траектория")


    class Meta:
        unique_together = ('user', 'trajectory')
        verbose_name = 'Траектория пользователя'
        verbose_name_plural = 'Траектории пользователей'
        indexes = [
            models.Index(fields=['user', 'trajectory'], name='uct_user_trajectory_idx'),
        ]


    def __str__(self) -> str:
        return f"{self.user.username} — {self.trajectory.name}"




class Certificate(models.Model):
    """
    Модель для хранения выданных сертификатов пользователям.
    """
    
    CERTIFICATE_TYPE_CHOICES = [
        ('course', 'За курс'),
        ('trajectory', 'За траекторию'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPE_CHOICES, verbose_name="Тип сертификата")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Курс", related_name='certificates')
    trajectory = models.ForeignKey(Trajectory, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Траектория", related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата выдачи")
    certificate_id = models.CharField(max_length=50, unique=True, verbose_name="Уникальный номер сертификата")
    

    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        ordering = ['-issued_at']
        unique_together = [
            ('user', 'course'),
            ('user', 'trajectory'),
        ]
        indexes = [
            models.Index(fields=['user', 'certificate_type'], name='cert_user_type_idx'),
            models.Index(fields=['certificate_id'], name='cert_id_idx'),
        ]
    

    def save(self, *args, **kwargs):
        """Генерирует `certificate_id`, если не заполнен."""
        if not self.certificate_id:
            # Генерируем уникальный ID сертификата
            import uuid
            self.certificate_id = f"CERT-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    

    def __str__(self):
        if self.certificate_type == 'course':
            return f"Сертификат {self.user.username} за курс {self.course.title}"
        else:
            return f"Сертификат {self.user.username} за траекторию {self.trajectory.name}"




class MetricsSubmission(models.Model):
    """
    Модель для хранения данных форм метрик эффективности клиник
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    clinic_name = models.CharField(max_length=255, verbose_name="Название клиники")
    initial_month = models.CharField(max_length=7, verbose_name="Начальный месяц")  # YYYY-MM
    doctors_count = models.PositiveIntegerField(verbose_name="Количество врачей")
    chairs_count = models.PositiveIntegerField(verbose_name="Количество кресел")
    # График работы
    hours_weekdays = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Часы работы в будни", default=0)
    hours_saturday = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Часы работы в субботу", default=0)
    hours_sunday = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Часы работы в воскресенье", default=0)
    
    # Дни в месяце для каждого из 6 месяцев
    days_month_1 = models.PositiveIntegerField(verbose_name="Дни месяц 1")
    days_month_2 = models.PositiveIntegerField(verbose_name="Дни месяц 2")
    days_month_3 = models.PositiveIntegerField(verbose_name="Дни месяц 3")
    days_month_4 = models.PositiveIntegerField(verbose_name="Дни месяц 4")
    days_month_5 = models.PositiveIntegerField(verbose_name="Дни месяц 5")
    days_month_6 = models.PositiveIntegerField(verbose_name="Дни месяц 6")
    
    # Данные врачей и их метрики сохраняются в JSON
    doctors_data = models.JSONField(verbose_name="Данные врачей", help_text="JSON с данными врачей и их метриками")
    
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    
    class Meta:
        verbose_name = 'Заполненная форма метрик'
        verbose_name_plural = 'Заполненные формы метрик'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', 'submitted_at'], name='metrics_user_date_idx'),
            models.Index(fields=['submitted_at'], name='metrics_date_idx'),
        ]
    
    def __str__(self):
        return f"Метрики {self.clinic_name} от {self.user.username} ({self.submitted_at.strftime('%d.%m.%Y')})"


