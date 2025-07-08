from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone

from unidecode import unidecode

from quizzes.models import Quiz
from builder.models import CategoryName

class Course(models.Model):
    """
    Модель представляющая таблицу myapp_course с курсами.

    Attrs:
        title (CharField) - заголовок курса
        description (TextField) - описание курса
        allowed_groups (ManyToMany) - группы пользователей, которым автоматически назначентся выбранный курс.
        
    """
   
    title = models.CharField(max_length=200, verbose_name="Название курса")
    description = CKEditor5Field('Описание курса', config_name='noTablesImages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    image = models.ImageField(upload_to='course_images/', blank=True, null=True, verbose_name="Изображение курса")
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

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_course_per_author'
            )
        ]


    def save(self, *args, **kwargs):
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
        course - Внешний ключ на курс к которому относится урок.
        title - название урока.
        content - содержимое урока. Заполняется администратором сайта.
        video_id - идентификатор прикрепленного видео из рутуб. Максимальное количество символов для передачи в форму 
                    задается параметром max_length.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='lessons', verbose_name="Курс")
    title = models.CharField(max_length=200, verbose_name="Название урока")
    content = CKEditor5Field('Content', config_name='extends')
    video_id = models.CharField(
        max_length=100, 
        verbose_name="ID видео с Rutube", 
        blank=True, 
        null=True,
        help_text="Пример: https://rutube.ru/video/VIDEO_ID/ - вводите только VIDEO_ID"
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


    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']
        indexes = [
            models.Index(fields=['course', 'order'], name='lesson_course_order_idx'),
        ]

    def get_previous_lesson(self):
        return Lesson.objects.filter(
            course=self.course, 
            order__lt=self.order
        ).order_by('-order').first()

    def get_next_lesson(self):
        return Lesson.objects.filter(
            course=self.course, 
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

    class Meta:
        verbose_name = 'Траектория курсов'
        verbose_name_plural = 'Траектории курсов'

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