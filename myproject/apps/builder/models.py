from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json


class CategoryName(models.Model):
    """Иерархическая категория для структуры БЗ (родитель/подкатегории, порядок, доступ)."""
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
    allowed_groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='allowed_categories',
        verbose_name='Доступен для групп',
        help_text='Группы, которым доступна эта категория и все её подкатегории/уроки в БЗ'
    )

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
        ('informational', 'Информационный'),
        ('educational', 'Обучающий'),
    ]
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('accepted', 'Принят'),
        ('assigned', 'Назначен'),
        ('studies_completed', 'Обучение завершено'),
        ('resolved', 'Завершён'),
        ('declined', 'Отклонён')
    ]
    title = models.CharField(max_length=255, verbose_name='Название инцидента')
    description = models.TextField(max_length=1000, blank=True, null=True, verbose_name='Описание проблемы')
    incident_type = models.CharField(max_length=32, choices=INCIDENT_TYPE_CHOICES, verbose_name='Тип инцидента')
    responsible_mentor = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Проверяющий наставник', related_name='mentored_incidents', blank=True, null=True)
    mentors_time_to_check = models.PositiveIntegerField(default=2, verbose_name="Время на проверку (дней)", help_text="Количество дней для проверки наставником")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='created_incidents', verbose_name='Кто зафиксировал')
    assigned_to = models.ManyToManyField(get_user_model(), related_name='assigned_incidents', blank=True, verbose_name='Кому назначен')
    violators = models.ManyToManyField(get_user_model(), related_name='violator_incidents', blank=True, verbose_name='Виновник/нарушитель инцидента')
    assigned_to_time_to_complete= models.PositiveIntegerField(default=3, verbose_name='Время на завершение обучения (дней)', blank=True, null=True, help_text="Количество дней для завершения обучения назначенными/нарушителями")
    expert = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='course_expert', verbose_name='Ответственный за актуальность курса', blank=True, null=True)
    expert_time_to_complete = models.PositiveIntegerField(default=3, verbose_name='Время на завершение/актуализацию (дней)', blank=True, null=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    previous_status = models.CharField(max_length=32, choices=STATUS_CHOICES, blank=True, null=True, verbose_name='Предыдущий статус', help_text='Статус до отклонения')
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата решения")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Дедлайн")
    
    # Связь с курсом-инцидентом
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents',
        verbose_name='Курс-инцидент'
    )
    

    
    class Meta:
        indexes = [
            models.Index(fields=['user'], name='incident_user_idx'),
            models.Index(fields=['status'], name='incident_status_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_incident_type_display()})"
 


class IPR(models.Model):
    """
    Индивидуальный План Развития (ИПР) для пользователя.
    Связывает пользователя с его планом развития и отслеживает прогресс по курсам.
    """
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('active', 'Активен'),
        ('completed', 'Завершен'),
        ('paused', 'Приостановлен'),
        ('cancelled', 'Отменен'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='iprs', verbose_name='Пользователь')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = 'ИПР'
        verbose_name_plural = 'ИПР'
        indexes = [
            models.Index(fields=['user'], name='ipr_user_idx'),
            models.Index(fields=['status'], name='ipr_status_idx'),
        ]
    
    def __str__(self) -> str:
        return f"ИПР для {self.user.get_full_name() or self.user.username} ({self.get_status_display()})"
    
    def get_active_modules_count(self):
        """Возвращает количество активных модулей ИПР"""
        from django.utils import timezone
        now = timezone.now()
        # Активные: модули со статусом 'active' и дедлайн либо не установлен, либо еще не прошел
        return self.modules.filter(
            status='active'
        ).filter(
            Q(deadline__isnull=True) | Q(deadline__gte=now)
        ).count()
    
    def get_overdue_modules_count(self):
        """Возвращает количество просроченных модулей ИПР"""
        from django.utils import timezone
        # Просроченные: модули со статусом 'active' и дедлайн установлен и уже прошел
        return self.modules.filter(
            status='active'
        ).filter(
            deadline__isnull=False,
            deadline__lt=timezone.now()
        ).count()
    
    def get_completed_modules_count(self):
        """Возвращает количество завершенных модулей ИПР"""
        # Завершенные: модули со статусом 'completed'
        return self.modules.filter(
            status='completed'
        ).count()
    
    def get_nearest_deadline(self):
        """Возвращает ближайший дедлайн из модулей ИПР"""
        from django.utils import timezone
        # Ближайший дедлайн из активных модулей (со статусом 'active' и с дедлайном в будущем)
        nearest = self.modules.filter(
            status='active',
            deadline__isnull=False,
            deadline__gte=timezone.now()
        ).order_by('deadline').first()
        return nearest.deadline if nearest else None


class IPRModule(models.Model):
    """
    Модуль ИПР (Индивидуального Плана Развития).
    Представляет отдельный модуль обучения в рамках ИПР пользователя.
    """
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('active', 'Активен'),
        ('completed', 'Завершен'),
        ('paused', 'Приостановлен'),
        ('cancelled', 'Отменен'),
    ]


    ipr = models.ForeignKey(IPR, on_delete=models.CASCADE, related_name='modules', verbose_name='ИПР')
    start_date = models.DateField(null=True, blank=True, verbose_name='Дата начала ИПР')
    end_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания ИПР')
    title = models.CharField(max_length=255, verbose_name='Тема ИПР (название модуля)')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='ipr_modules', verbose_name='ФИО')
    department = models.ForeignKey('auth.Group', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Отделение (группа)')
    supervisor = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_ipr_modules', verbose_name='Руководитель')
    department_head = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='department_head_ipr_modules', verbose_name='Зав отделением')
    mentor = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='mentored_ipr_modules', verbose_name='Наставник')
    diagnostics = models.TextField(blank=True, null=True, verbose_name='Диагностика / Проблема', help_text='Описание проблем и диагностики')
    goals = models.TextField(blank=True, null=True, verbose_name='Цели', help_text='Описание целей модуля ИПР')
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='new', verbose_name='Статус', help_text='Пока прочерк')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий', help_text='Произвоьные комментарии по факту выполненной работы')
    intermediate_control = models.CharField(max_length=255, blank=True, null=True, verbose_name='Промежуточный контроль', help_text='Пока прочерк')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн', help_text='Пока прочерк')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = 'Модуль ИПР'
        verbose_name_plural = 'Модули ИПР'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ipr'], name='iprmodule_ipr_idx'),
            models.Index(fields=['user'], name='iprmodule_user_idx'),
            models.Index(fields=['mentor'], name='iprmodule_mentor_idx'),
            models.Index(fields=['supervisor'], name='iprmodule_supervisor_idx'),
            models.Index(fields=['department_head'], name='iprmodule_dept_head_idx'),
        ]
    
    def __str__(self) -> str:
        return f"{self.title} - {self.user.get_full_name() or self.user.username}"




class IPRModuleIndicator(models.Model):
    """
    Показатель модуля ИПР.
    Хранит информацию о показателях эффективности для модуля ИПР.
    """
    module = models.ForeignKey(IPRModule, on_delete=models.CASCADE, related_name='indicators', verbose_name='Модуль ИПР')
    name = models.CharField(max_length=255, verbose_name='Показатель', help_text='Название показателя')
    point_a = models.TextField(blank=True, null=True, verbose_name='Точка А', help_text='Начальное состояние')
    intermediate_point = models.TextField(blank=True, null=True, verbose_name='Промежуточная точка', help_text='Промежуточное состояние')
    stage_deadline = models.DateTimeField(null=True, blank=True, verbose_name='Срок этапа', help_text='Дата и время срока этапа')
    point_b = models.TextField(blank=True, null=True, verbose_name='Точка Б', help_text='Целевое состояние')
    fact = models.TextField(blank=True, null=True, verbose_name='Факт', help_text='Фактическое состояние')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн', help_text='Дата и время дедлайна')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок', help_text='Порядок отображения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = 'Показатель модуля ИПР'
        verbose_name_plural = 'Показатели модулей ИПР'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['module'], name='iprmoduleindicator_module_idx'),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.module.title}"




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




class DictionarySection(models.Model):
    """Раздел словаря терминов (верхний уровень группировки терминов)."""
    name = models.CharField(max_length=200, verbose_name="Название отдела")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    # Можно добавить slug, описание и т.д.

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Отдел словаря"
        verbose_name_plural = "Отделы словаря"

    def __str__(self):
        return self.name




class DictionaryTerm(models.Model):
    """Элемент словаря: термин, сленг, определение, опциональное фото и автор."""
    section = models.ForeignKey(DictionarySection, on_delete=models.CASCADE, blank=True, null=True, related_name='terms', verbose_name="Отдел")
    term = models.CharField(max_length=200, verbose_name="Термин")
    slang = models.CharField(max_length=200, blank=True, verbose_name="Сленг")
    definition = models.TextField(verbose_name="Определение")
    photo = models.ImageField(upload_to='dict_photos/', blank=True, null=True, verbose_name="Фото")
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

 
 
 
class LessonAllowedRole(models.Model):
    """
    Модель для связи уроков с разрешенными должностями для актуализации.
    Позволяет ограничить список должностей, которые могут быть назначены ответственными
    при актуализации конкретного урока.
    """
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='allowed_roles', verbose_name='Урок')
    role = models.ForeignKey('users.Role', on_delete=models.CASCADE, verbose_name='Должность')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        unique_together = ('lesson', 'role')
        verbose_name = 'Разрешенная должность для урока'
        verbose_name_plural = 'Разрешенные должности для уроков'
        ordering = ['role__name']

    def __str__(self):
        return f"{self.lesson.title} - {self.role.name}"

    @property
    def responsible_fio(self):
        """Возвращает ФИО ответственного за данную должность"""
        if self.role.responsible_user:
            return self.role.responsible_user.get_full_name()
        return "— не назначен —"


 
 
 
 
class AuditLog(models.Model):
    """
    Модель для логирования всех операций в базе знаний
    """
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Изменение'),
        ('delete', 'Удаление'),
        ('copy', 'Копирование'),
        ('move', 'Перемещение'),
        ('mirror', 'Создание зеркала'),
        ('reorder', 'Изменение порядка'),
        ('actualize', 'Актуализация'),
    ]
    
    # Кто выполнил действие
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name='Пользователь'
    )
    
    # Когда выполнено
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    
    # Тип действия
    action = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES, 
        verbose_name='Действие'
    )
    
    # Объект, над которым выполнено действие (Generic FK)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Название объекта (для случаев когда объект удален)
    object_name = models.CharField(max_length=255, verbose_name='Название объекта')
    
    # Модель объекта
    model_name = models.CharField(max_length=100, verbose_name='Модель')
    
    # IP адрес пользователя
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адрес')
    
    # Дополнительные данные в JSON
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='Дополнительные данные')
    
    # Данные до изменения (для update)
    old_values = models.JSONField(default=dict, blank=True, verbose_name='Старые значения')
    
    # Данные после изменения (для create/update)
    new_values = models.JSONField(default=dict, blank=True, verbose_name='Новые значения')
    
    # Комментарий к действию
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    
    class Meta:
        verbose_name = 'Запись аудита'
        verbose_name_plural = 'Записи аудита'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user'], name='auditlog_user_idx'),
            models.Index(fields=['timestamp'], name='auditlog_timestamp_idx'),
            models.Index(fields=['action'], name='auditlog_action_idx'),
            models.Index(fields=['content_type', 'object_id'], name='auditlog_object_idx'),
            models.Index(fields=['model_name'], name='auditlog_model_idx'),
        ]
    
    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'Система'
        return f"{user_name} - {self.get_action_display()} - {self.object_name} ({self.timestamp.strftime('%d.%m.%Y %H:%M')})"
    
    def get_changes_summary(self):
        """Возвращает краткое описание изменений"""
        if self.action == 'update' and self.old_values and self.new_values:
            # Парсим JSON, если значения являются строками
            old_values = self.old_values
            new_values = self.new_values
            if isinstance(old_values, str):
                try:
                    old_values = json.loads(old_values)
                except (json.JSONDecodeError, TypeError):
                    return ''
            if isinstance(new_values, str):
                try:
                    new_values = json.loads(new_values)
                except (json.JSONDecodeError, TypeError):
                    return ''
            
            # Проверяем, что значения являются словарями
            if not isinstance(old_values, dict) or not isinstance(new_values, dict):
                return ''
            
            changes = []
            for field, new_value in new_values.items():
                old_value = old_values.get(field)
                if old_value != new_value:
                    changes.append(f"{field}: '{old_value}' → '{new_value}'")
            return '; '.join(changes)
        return ''