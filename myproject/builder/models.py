from django.db import models
from django.contrib.auth import get_user_model


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