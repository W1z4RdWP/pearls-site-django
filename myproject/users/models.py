from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from typing import Any

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
    first_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Отчество")
    date_of_birth = models.DateField(verbose_name="Дата рождения", blank=True, null=True)
    phone_number = models.CharField(
        max_length=20,
        verbose_name="Номер телефона",
        blank=True,
        null=True,
        help_text="Введите номер в формате +7XXXXXXXXXX"
    )
    # group = models.ForeignKey(
    #     Group,
    #     on_delete=models.SET_NULL,
    #     blank=True,
    #     null=True,
    #     verbose_name="Группа (роль)"
    # )
    image = models.ImageField(default='profile_pics/default.jpg', upload_to='profile_pics')
    bio = models.TextField(max_length=500, blank=True, null=True, verbose_name="О себе")
    is_approved = models.BooleanField(default=False, verbose_name="Подвтерждение администратором")

    class Meta:
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