from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from typing import Any

from gamification.models import Badge
from myapp.models import UserCourse


class Role(models.Model):
    """
    Модель должности.

    Attributes:
        name (CharField): Название должности.
        responsible_user (OneToOneField): Связь с моделью User.
    """
    name = models.CharField(max_length=200, unique=True, verbose_name="Название должности")
    responsible_user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Ответственный",
        help_text="Пользователь, ответственный за данную должность"
    )

    class Meta:
        app_label = 'users'
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.responsible_user and self.responsible_user.profile.role != self:
            raise ValidationError(
                f'Пользователь {self.responsible_user.get_full_name()} не имеет должности "{self.name}"'
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Department(models.Model):
    """
    Модель подразделения.

    Attributes:
        name (CharField): Название подразделения.
    """
    name = models.CharField(max_length=200, unique=True, verbose_name="Название подразделения")

    class Meta:
        app_label = 'users'
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


        

class Profile(models.Model):
    """
    Модель профиля пользователя.

    Attributes:
        user (User): Связь один-к-одному с моделью User.
        first_name (CharField): Имя пользователя, сейчас является необязательным аттрибутом, но при сбросе БД, следует изменить на обязательное
        last_name (CharField): Фамилия пользователя, сейчас является необязательным аттрибутом, но при сбросе БД, следует изменить на обязательное
        role (ForeignKey): Связь с моделью Role (Должность).
        middle_name (CharField): Отчество пользователя, является необязательным аттрибутом.
        date_of_birth (DateField): Дата рождения
        phone_number (CharField): Номер телефона в формате +7XXXXXXXXXX
        image (ImageField): Изображение профиля. По умолчанию используется 'profile_pics/default.jpg'.
        bio (TextField): Текстовое поле с информацией о пользователе.
        dascoin_points (PositiveIntegerField): Баллы DASCOIN.
        is_mentor (BooleanField): Провряет, является ли пользователь наставником.
        is_approved (BooleanField): Провряет, подтвердил ли администратор регистрацию пользователя.

    Methods:
        add_dascoin_points(points: int, reason: str = "") -> None: Добавляет баллы DASCOIN пользователю.
        get_badges() -> QuerySet: Возвращает все бейджи пользователя.
        get_achievements() -> QuerySet: Возвращает все достижения пользователя.
        get_recent_badges(limit: int = 8) -> QuerySet: Возвращает последние полученные бейджи.
        get_recent_achievements(limit: int = 8) -> QuerySet: Возвращает последние полученные достижения.
        is_mentor_user() -> bool: Проверяет, является ли пользователь наставником.
        is_responsible() -> bool: Проверяет, является ли пользователь ответственным за свою должность.
        clean() -> None: Проверяет, что пользователь имеет должность, которую он занимает.
        save() -> None: Сохраняет профиль пользователя.
        __str__() -> str: Возвращает строковое представление профиля.
        is_mentor_user() -> bool: Проверяет, является ли пользователь наставником.
        is_responsible() -> bool: Проверяет, является ли пользователь ответственным за свою должность.

    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Отчество")
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Должность")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Подразделение")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    country = models.CharField(max_length=200, blank=True, null=True, verbose_name="Страна")
    phone_number = models.CharField(
        max_length=18,
        verbose_name="Номер телефона",
        blank=True,
        null=True,
        help_text="Введите номер в формате +7XXXXXXXXXX"
    )
    phone_arbitrary_format = models.BooleanField(
        default=False,
        verbose_name="Произвольный формат телефона",
        help_text="Разрешить произвольный формат номера телефона"
    )
    image = models.ImageField(default='profile_pics/default.jpg', upload_to='profile_pics', verbose_name="Аватар")
    bio = models.TextField(max_length=500, blank=True, null=True, verbose_name="О себе")
    is_approved = models.BooleanField(default=False, verbose_name="Подвтерждение администратором")
    is_mentor = models.BooleanField(default=False, verbose_name="Является наставником", help_text="Пользователь с правами наставника")
    dascoin_points = models.PositiveIntegerField(default=0, verbose_name="Баллы DASCOIN")
    first_login_shown = models.BooleanField(default=False, verbose_name="Показано модальное окно при первом входе")

    class Meta:
        app_label = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['user']

    def __str__(self) -> str:
        """
        Возвращает строковое представление профиля.

        Returns:
            str: Учётная запись и имя пользователя.
        """
                
        return f'Учётная запись {self.user.username}'
    



    @property
    def is_mentor_user(self) -> bool:
        """
        Проверяет, является ли пользователь наставником.
        """
        return self.is_mentor

    @property
    def is_responsible(self) -> bool:
        """
        Проверяет, является ли пользователь ответственным за свою должность.
        """
        return self.role and self.role.responsible_user == self.user
    
    def add_dascoin_points(self, points: int, reason: str = "") -> None:
        """
        Добавляет баллы DASCOIN пользователю.
        
        Args:
            points (int): Количество баллов для добавления
        """

        self._dascoin_reason = reason
        self.dascoin_points += points
        self.save()
    
    def get_available_badges_count(self):
        """
        Возвращает количество доступных бейджей, которые пользователь может получить.
        Доступные бейджи - это бейджи за курсы, которые назначены пользователю,
        но еще не завершены.
        """
        # Получаем все курсы, назначенные пользователю
        assigned_courses = UserCourse.objects.filter(user=self.user)
        
        assigned_courses_count = assigned_courses.count()

        # Получаем курсы, которые пользователь уже завершил
        completed_course_ids = assigned_courses.filter(status='completed').values_list('course_id', flat=True)

        # Получаем курсы, которые еще не завершены
        uncompleted_courses_count = assigned_courses.exclude(course_id__in=completed_course_ids).count()

        # Получаем бейджи, которые пользователь уже получил
        earned_badge_names = self.get_badges().values_list('badge__name', flat=True)

        # Получаем общие бейджи (не связанные с курсами)
        general_badges_count = Badge.objects.filter(
            is_active=True,
            badge_type__in=['points', 'skill', 'trajectory']
        ).count()

        # Общее количество доступных бейджей = бейджи за незавершенные курсы + общие бейджи
        return assigned_courses_count + general_badges_count

    def get_badges(self):
        """Возвращает все бейджи пользователя"""
        from gamification.models import UserBadge
        return UserBadge.objects.filter(user=self.user).select_related('badge')
    
    def get_achievements(self):
        """Возвращает все достижения пользователя"""
        from gamification.models import UserAchievement
        return UserAchievement.objects.filter(user=self.user).select_related('achievement')
    
    def get_recent_badges(self, limit=8):
        """Возвращает последние полученные бейджи"""
        return self.get_badges()[:limit]
    
    def get_recent_achievements(self, limit=8):
        """Возвращает последние полученные достижения"""
        return self.get_achievements()[:limit]


@receiver(post_save, sender=User)
def create_profile(sender: Any, instance: User, created: bool, **kwargs: Any) -> None:
    """
    Сигнал для автоматического создания профиля при создании пользователя.

    Args:
        sender (Any): Модель, отправившая сигнал.
        instance (User): Экземпляр модели User.
        created (bool): Флаг, указывающий, был ли объект создан.
        **kwargs (Any): Дополнительные аргументы.
    """
        
    if created:
        Profile.objects.create(user=instance)




@receiver(post_save, sender=User)
def save_profile(sender: Any, instance: User, **kwargs: Any) -> None:
    """
    Сигнал для автоматического сохранения профиля при сохранении пользователя.
    

    Args:
        sender (Any): Модель, отправившая сигнал.
        instance (User): Экземпляр модели User.
        **kwargs (Any): Дополнительные аргументы.
    """

    profile = instance.profile
    profile.save()