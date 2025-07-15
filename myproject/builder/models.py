from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings


class CategoryName(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название категории")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Родительская категория"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['parent'], name='categoryname_parent_idx'),
        ]

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' / '.join(full_path[::-1])

class Document(models.Model):
    """
    Документ для базы знаний. Может быть привязан к уроку или использоваться отдельно.
    """
    title = models.CharField(max_length=255, verbose_name='Название документа')
    file = models.FileField(upload_to='documents/', verbose_name='Файл')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Загружен')

    def __str__(self) -> str:
        return self.title

class Incident(models.Model):
    """
    Инцидент, связанный с обучением или ошибкой. Может автоматически назначать материалы и тесты.
    """
    INCIDENT_TYPE_CHOICES = [
        ('test_fail', 'Провал теста'),
        ('incident', 'Инцидент'),
        ('regulation_change', 'Изменение регламента'),
    ]
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('resolved', 'Решён'),
    ]
    title = models.CharField(max_length=255, verbose_name='Название инцидента')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Сотрудник')
    incident_type = models.CharField(max_length=32, choices=INCIDENT_TYPE_CHOICES, verbose_name='Тип инцидента')
    description = models.TextField(verbose_name='Описание', blank=True)
    related_documents = models.ManyToManyField('Document', blank=True, verbose_name='Документы из БЗ')
    role = models.CharField(max_length=128, verbose_name='Роль', blank=True)
    error_type = models.CharField(max_length=128, verbose_name='Тип ошибки', blank=True)
    topic = models.CharField(max_length=128, verbose_name='Тема', blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        indexes = [
            models.Index(fields=['user'], name='incident_user_idx'),
            models.Index(fields=['status'], name='incident_status_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_incident_type_display()})"

class LessonVersion(models.Model):
    """
    Версия урока базы знаний. Хранит историю изменений для каждого Lesson.
    version — автоинкремент по каждому уроку (v1, v2, ...)
    updated_by — пользователь, внёсший изменение (ФИО берём из user.get_full_name()).
    next_update — дата следующей актуализации (может быть пустой)
    update_period_days — стандартный период между актуализациями (по умолчанию 90 дней)
    """
    lesson: 'Lesson' = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='versions', verbose_name='Урок')
    version: int = models.PositiveIntegerField(verbose_name='Номер версии')
    title: str = models.CharField(max_length=200, verbose_name='Название урока')
    content: str = models.TextField(verbose_name='Содержимое')
    video_id: str = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID видео с Rutube')
    updated_at: 'datetime' = models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения')
    updated_by: settings.AUTH_USER_MODEL = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Кто изменил')
    comment: str = models.CharField(max_length=255, blank=True, verbose_name='Комментарий к изменению')
    next_update: 'date' = models.DateField(null=True, blank=True, verbose_name='Дата следующего обновления')
    update_period_days: int = models.IntegerField(default=90, verbose_name='Стандарт периода обновлений, дней')

    class Meta:
        verbose_name = 'Версия урока'
        verbose_name_plural = 'Версии уроков'
        ordering = ['-version', '-updated_at']
        unique_together = ('lesson', 'version')

    def __str__(self) -> str:
        return f"{self.lesson.title} v{self.version} ({self.updated_at:%d.%m.%Y})"


class LessonCategoryMirror(models.Model):
    """
    Зеркальная ссылка на урок (Lesson) в другой категории (CategoryName).
    Позволяет размещать один и тот же урок в нескольких категориях (аналог симлинка).
    При удалении урока — все зеркала удаляются (CASCADE).
    При удалении категории — только связь.
    """
    lesson: 'Lesson' = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='mirrors', verbose_name='Зеркалируемый урок')
    category: CategoryName = models.ForeignKey(CategoryName, on_delete=models.CASCADE, related_name='mirrored_lessons', verbose_name='Категория зеркала')
    order: int = models.PositiveIntegerField(default=0, verbose_name='Порядок в категории')

    class Meta:
        unique_together = ('lesson', 'category')
        verbose_name = 'Зеркало урока'
        verbose_name_plural = 'Зеркала уроков'
        ordering = ['order']

    def __str__(self) -> str:
        return f"Зеркало: {self.lesson.title} в {self.category}"


class DictionaryTerm(models.Model):
    term = models.CharField(max_length=200, verbose_name="Термин")
    definition = models.TextField(verbose_name="Определение")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Автор")

    class Meta:
        ordering = ['order', 'term']
        verbose_name = "Слово словаря"
        verbose_name_plural = "Словарь"

    def __str__(self):
        return self.term