from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class Notification(models.Model):
    """
    Модель для хранения уведомлений пользователей
    """
    NOTIFICATION_TYPES = [
        ('dascoin', 'Начисление/списание DASCOIN'),
        ('course_assigned', 'Назначение курса'),
        ('trajectory_assigned', 'Назначение траектории'),
        ('platform_update', 'Обновление платформы'),
        ('course_reminder', 'Напоминание о курсе'),
        ('lesson_actualization', 'Напоминание об актуализации урока'),
        # Новые типы: техподдержка
        ('ticket_status', 'Изменение статуса тикета'),
        ('ticket_comment', 'Новое сообщение по тикету'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, verbose_name="Тип уведомления")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    message = models.TextField(verbose_name="Сообщение")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    # Дополнительные поля для разных типов уведомлений
    related_course = models.ForeignKey(
        'courses.Course', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="Связанный курс"
    )
    related_trajectory = models.ForeignKey(
        'courses.Trajectory', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="Связанная траектория"
    )
    related_lesson = models.ForeignKey(
        'courses.Lesson', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="Связанный урок"
    )
    related_ticket = models.ForeignKey(
        'tech_support.Ticket',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Связанный тикет"
    )
    points_change = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Изменение баллов DASCOIN"
    )
    
    class Meta:
        app_label = 'notifications'
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def get_absolute_url(self):
        """Возвращает URL для перехода к связанному объекту"""
        if self.notification_type == 'course_assigned' and self.related_course:
            return reverse('courses:course_detail', kwargs={'slug': self.related_course.slug})
        elif self.notification_type == 'trajectory_assigned' and self.related_trajectory:
            return reverse('courses:trajectory_detail', kwargs={'pk': self.related_trajectory.pk})
        elif self.notification_type == 'lesson_actualization' and self.related_lesson:
            return reverse('courses:lesson_detail', kwargs={'pk': self.related_lesson.pk})
        # Новые маршруты для тикетов
        elif self.notification_type in ('ticket_status', 'ticket_comment') and self.related_ticket:
            return reverse('tech_support:ticket_detail', kwargs={'pk': self.related_ticket.pk})
        return '#'
    
    @classmethod
    def create_dascoin_notification(cls, user, points_change, reason=None, message=None):
        """Создает уведомление о изменении баллов DASCOIN"""
        if points_change > 0:
            title = f"Начислено {points_change} баллов DASCOIN"
            if reason:
                title += f" за {reason}"
        else:
            title = f"Списано {abs(points_change)} баллов DASCOIN"
            if reason:
                title += f" за {reason}"
        
        if not message:
            message = title
        
        return cls.objects.create(
            user=user,
            notification_type='dascoin',
            title=title,
            message=message,
            points_change=points_change
        )
    
    @classmethod
    def create_course_assignment_notification(cls, user, course):
        """Создает уведомление о назначении курса"""
        notification = cls.objects.create(
            user=user,
            notification_type='course_assigned',
            title=f"Вам назначен курс",
            message=f"Вам назначен курс «{course.title}»",
            related_course=course
        )
        
        # НЕ отправляем email отсюда - email отправляется из сигналов courses/signals.py
        # чтобы избежать дублирования и правильно обрабатывать случаи с траекториями
        
        return notification
    
    @classmethod
    def create_trajectory_assignment_notification(cls, user, trajectory):
        """Создает уведомление о назначении траектории"""
        notification = cls.objects.create(
            user=user,
            notification_type='trajectory_assigned',
            title=f"Вам назначена траектория",
            message=f"Вам назначена траектория «{trajectory.name}»",
            related_trajectory=trajectory
        )
        
        # НЕ отправляем email отсюда - email отправляется из сигналов courses/signals.py
        # чтобы избежать дублирования
        
        return notification
    
    @classmethod
    def create_platform_update_notification(cls, user, title, message):
        """Создает уведомление об обновлении платформы"""
        return cls.objects.create(
            user=user,
            notification_type='platform_update',
            title=title,
            message=message
        )
    
    @classmethod
    def create_course_reminder_notification(cls, user, course):
        """Создает напоминание о курсе"""
        return cls.objects.create(
            user=user,
            notification_type='course_reminder',
            title="Напоминание о курсе",
            message=f"Не забудьте пройти курс «{course.title}»",
            related_course=course
        )
    
    @classmethod
    def create_lesson_actualization_notification(cls, user, lesson, actualization_date):
        """Создает напоминание об актуализации урока"""
        return cls.objects.create(
            user=user,
            notification_type='lesson_actualization',
            title="Напоминание об актуализации",
            message=f"Приближается дата актуализации для урока «{lesson.title}» - {actualization_date.strftime('%d.%m.%Y')}",
            related_lesson=lesson
        )
    
    # Новые helpers для тикетов
    @classmethod
    def create_ticket_status_notification(cls, user, ticket, old_status_name, new_status_name):
        title = f"Статус тикета {ticket.ticket_number} изменён: {old_status_name} → {new_status_name}"
        message = f"Тикет: {ticket.title}\nБыл: {old_status_name}\nСтал: {new_status_name}"
        return cls.objects.create(
            user=user,
            notification_type='ticket_status',
            title=title,
            message=message,
            related_ticket=ticket,
        )
    
    @classmethod
    def create_ticket_comment_notification(cls, user, ticket, author, comment_text):
        author_name = author.get_full_name() or author.username
        title = f"Новый комментарий в тикете {ticket.ticket_number}"
        message = f"{author_name}: {comment_text[:400]}"
        return cls.objects.create(
            user=user,
            notification_type='ticket_comment',
            title=title,
            message=message,
            related_ticket=ticket,
        )
