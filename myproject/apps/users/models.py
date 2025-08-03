from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from typing import Any


class Role(models.Model):
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


        

class Profile(models.Model):
    """
    Модель профиля пользователя.

    Attributes:
        user (User): Связь один-к-одному с моделью User.
        first_name (CharField): Имя пользователя, сейчас является необязательным аттрибутом, но при сбросе БД, следует изменить на обязательное
        last_name (CharField): Фамилия пользователя, сейчас является необязательным аттрибутом, но при сбросе БД, следует изменить на обязательное
        middle_name (CharField): Отчество пользователя, является необязательным аттрибутом.
        date_of_birth (DateField): Дата рождения
        phone_number (CharField): Номер телефона в формате +7XXXXXXXXXX
        image (ImageField): Изображение профиля. По умолчанию используется 'profile_pics/default.jpg'.
        bio (TextField): Текстовое поле с информацией о пользователе.
        is_approved (BooleanField): Провряет, подтвердил ли администратор регистрацию пользователя.

    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Отчество")
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Должность")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
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
    dascoin_points = models.PositiveIntegerField(default=0, verbose_name="Баллы DASCOIN")

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
    def exp(self) -> int:
        """
        Динамически считает опыт пользователя:
        +150 за каждый завершённый курс (+10% если есть финальный тест)
        +500 за каждую завершённую траекторию
        """
        from myapp.models import UserCourse
        from courses.models import UserCourseTrajectory
        exp = 0
        # Курсы
        for uc in UserCourse.objects.filter(user=self.user, status='completed'):
            base = 150
            if getattr(uc.course, 'final_quiz', None):
                base = int(base * 1.1)
            exp += base
        # Траектории
        for ut in UserCourseTrajectory.objects.filter(user=self.user, completed=True):
            exp += 500
        return exp

    @property
    def is_responsible(self) -> bool:
        """
        Проверяет, является ли пользователь ответственным за свою должность.
        """
        return self.role and self.role.responsible_user == self.user
    
    def add_dascoin_points(self, points: int) -> None:
        """
        Добавляет баллы DASCOIN пользователю.
        
        Args:
            points (int): Количество баллов для добавления
        """
        self.dascoin_points += points
        self.save()
    
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