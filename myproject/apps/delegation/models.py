from django.db import models
from django.contrib.auth.models import User, Permission
from django.utils import timezone
from django.db.models import Q


class Delegation(models.Model):
    """
    Модель делегирования полномочий.
    
    Attributes:
        delegator: Передающий - пользователь, который передает делегирование
        delegate: Принимающий - пользователь, который получает права
        delegated_permissions: Делегируемые права (текстовое поле для описания прав)
        start_datetime: Дата и время начала делегирования
        end_datetime: Дата и время окончания делегирования
        status: Статус делегирования
        comment: Причина делегирования (опционально)
        created_at: Дата создания записи
        confirmed_at: Дата подтверждения принимающим
        confirmed_by_assistant: Подтверждение бизнес-ассистентом
    """
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('active', 'Активно'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    
    COMMENT_CHOICES = [
        ('vacation', 'Отпуск'),
        ('sick_leave', 'Больничный'),
        ('replacement', 'Замена сотрудника'),
        ('other', 'Другое'),
    ]
    
    delegator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='delegations_given',
        verbose_name='Передающий'
    )
    delegate = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='delegations_received',
        verbose_name='Принимающий'
    )
    project = models.TextField(
        verbose_name='Проект',
        blank=True,
        null=True
    )
    closing_section = models.TextField(
        verbose_name='Какой участок закрывается',
        blank=True,
        null=True
    )
    restrictions = models.TextField(
        verbose_name='Ограничения',
        blank=True,
        null=True
    )
    delegated_permissions = models.TextField(
        verbose_name='Делегируемые права',
        help_text='Описание делегируемых прав и полномочий',
        blank=True,
        null=True
    )
    start_datetime = models.DateTimeField(
        verbose_name='Дата и время начала',
        help_text='С какого момента права становятся активными'
    )
    end_datetime = models.DateTimeField(
        verbose_name='Дата и время окончания',
        help_text='До какого момента права действуют'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    comment = models.CharField(
        max_length=20,
        choices=COMMENT_CHOICES,
        blank=True,
        null=True,
        verbose_name='Причина делегирования'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    confirmed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата подтверждения'
    )
    confirmed_by_assistant = models.BooleanField(
        default=False,
        verbose_name='Подтверждено бизнес-ассистентом'
    )
    
    class Meta:
        app_label = 'delegation'
        verbose_name = 'Делегирование'
        verbose_name_plural = 'Делегирования'
        ordering = ['-created_at']
        
    def __str__(self):
        try:
            delegator_name = self.delegator.get_full_name() or self.delegator.username
        except:
            delegator_name = 'Unknown'
        
        try:
            delegate_name = self.delegate.get_full_name() or self.delegate.username
        except:
            delegate_name = 'Unknown'
        
        return f'{delegator_name} → {delegate_name} ({self.get_status_display()})'
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Проверка: delegator и delegate должны быть установлены
        if not self.delegator_id or not self.delegate_id:
            return  # Пропускаем валидацию если поля еще не заполнены
        
        # Проверка: нельзя делегировать самому себе
        if self.delegator_id == self.delegate_id:
            raise ValidationError('Нельзя делегировать права самому себе')
        
        # Проверка: дата окончания должна быть позже даты начала
        if self.end_datetime and self.start_datetime and self.end_datetime <= self.start_datetime:
            raise ValidationError('Дата окончания должна быть позже даты начала')
    
    def save(self, *args, **kwargs):
        # Вызываем full_clean только если объект уже имеет все необходимые поля
        if self.delegator_id and self.delegate_id and self.start_datetime and self.end_datetime:
            self.clean()
        super().save(*args, **kwargs)
    
    def confirm(self):
        """Подтверждение делегирования принимающим"""
        if self.status == 'pending':
            self.status = 'active'
            self.confirmed_at = timezone.now()
            self.save()
            return True
        return False
    
    def reject(self):
        """Отклонение делегирования принимающим"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.save()
            return True
        return False
    
    def cancel(self):
        """Отмена делегирования передающим"""
        if self.status in ['pending', 'active']:
            self.status = 'cancelled'
            self.save()
            return True
        return False
    
    def is_active(self):
        """Проверка, активно ли делегирование в текущий момент"""
        now = timezone.now()
        return (
            self.status == 'active' and 
            self.start_datetime <= now <= self.end_datetime
        )
    
    def should_be_completed(self):
        """Проверка, должно ли делегирование быть завершено"""
        return self.status == 'active' and timezone.now() > self.end_datetime
    
    @classmethod
    def get_active_delegations_for_user(cls, user):
        """Получить все активные делегирования для пользователя (где он принимающий)"""
        now = timezone.now()
        return cls.objects.filter(
            delegate=user,
            status='active',
            start_datetime__lte=now,
            end_datetime__gte=now
        )
    
    @classmethod
    def get_recent_delegations(cls, user, days=30):
        """Получить делегирования за последние N дней для пользователя"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(
            Q(delegator=user) | Q(delegate=user),
            created_at__gte=cutoff_date
        )
