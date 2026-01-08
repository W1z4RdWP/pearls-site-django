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
        ('quiz_reviewed', 'Оценка теста наставником'),
        ('homework_reviewed', 'Оценка задания наставником'),
        ('order_status', 'Изменение статуса заказа'),
        ('course_materials_updated', 'Обновление материалов в завершенном курсе'),
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
    related_quiz_result = models.ForeignKey(
        'myapp.QuizResult',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Связанный результат теста"
    )
    related_order = models.ForeignKey(
        'shop.ProductOrder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Связанный заказ"
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
            # Для траекторий нужно найти UserCourseTrajectory для данного пользователя
            from courses.models import UserCourseTrajectory
            try:
                user_trajectory = UserCourseTrajectory.objects.get(
                    user=self.user, 
                    trajectory=self.related_trajectory
                )
                return reverse('courses:user_course_trajectory_detail', kwargs={'pk': user_trajectory.pk})
            except UserCourseTrajectory.DoesNotExist:
                return '#'
        elif self.notification_type == 'lesson_actualization' and self.related_lesson:
            return reverse('courses:lesson_detail', kwargs={'pk': self.related_lesson.pk})
        elif self.notification_type == 'dascoin':
            # Уведомления о DASCOIN ведут на историю транзакций
            return reverse('users:transactions')
        elif self.notification_type == 'platform_update':
            # Уведомления об обновлениях платформы ведут на changelog
            return reverse('changelog')
        # Новые маршруты для тикетов
        elif self.notification_type in ('ticket_status', 'ticket_comment') and self.related_ticket:
            return reverse('tech_support:ticket_detail', kwargs={'pk': self.related_ticket.pk})
        elif self.notification_type == 'quiz_reviewed' and self.related_quiz_result:
            # Получаем quiz_id из quiz_title
            from quizzes.models import Quiz
            quiz = Quiz.objects.filter(name=self.related_quiz_result.quiz_title).first()
            if quiz and self.related_quiz_result.course:
                return reverse('quizzes:quiz_best_result', kwargs={'quiz_id': quiz.id}) + f'?course_slug={self.related_quiz_result.course.slug}'
        elif self.notification_type == 'homework_reviewed' and self.related_course:
            # Уведомление о проверке задания ведет на страницу курса
            return reverse('courses:course_detail', kwargs={'slug': self.related_course.slug})
        elif self.notification_type == 'order_status' and self.related_order:
            # Уведомления о заказах ведут на страницу магазина
            return reverse('shop:shop')
        elif self.notification_type == 'course_materials_updated' and self.related_course:
            return reverse('courses:course_detail', kwargs={'slug': self.related_course.slug})
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
    
    @classmethod
    def create_quiz_reviewed_notification(cls, quiz_result):
        """Создает уведомление об оценке теста наставником"""
        from quizzes.models import Quiz
        quiz = Quiz.objects.filter(name=quiz_result.quiz_title).first()
        quiz_name = quiz.name if quiz else quiz_result.quiz_title
        
        title = "Тест проверен наставником"
        message = f"Ваш тест «{quiz_name}» был проверен наставником. "
        if quiz_result.mentor_comment:
            message += f"Комментарий: {quiz_result.mentor_comment[:200]}"
        else:
            message += f"Результат: {quiz_result.percent}%"
        
        return cls.objects.create(
            user=quiz_result.user,
            notification_type='quiz_reviewed',
            title=title,
            message=message,
            related_quiz_result=quiz_result,
        )
    
    @classmethod
    def create_order_status_notification(cls, order, old_status, new_status):
        """Создает уведомление об изменении статуса заказа"""
        status_messages = {
            'pending': 'ожидает подтверждения',
            'approved': 'одобрен',
            'rejected': 'отклонен',
            'completed': 'выполнен',
            'cancelled': 'отменен',
        }
        
        old_status_display = status_messages.get(old_status, old_status) if old_status else 'новый'
        new_status_display = status_messages.get(new_status, new_status)
        
        # Формируем заголовок и сообщение в зависимости от статуса
        if old_status is None and new_status == 'pending':
            # Заказ только что создан
            title = "Заказ оформлен"
            message = f"Ваш заказ товара «{order.product.name}» успешно оформлен. Списано {order.points_spent} баллов. HR проверяет соответствие политике в течение 2 рабочих дней."
        elif new_status == 'approved':
            title = "Заказ одобрен"
            message = f"Ваш заказ товара «{order.product.name}» был одобрен. Вы сможете получить товар в ближайшее время."
        elif new_status == 'rejected':
            title = "Заказ отклонен"
            message = f"Ваш заказ товара «{order.product.name}» был отклонен. Потраченные {order.points_spent} баллов возвращены на ваш счет."
            if order.admin_comment:
                message += f"\n\nКомментарий администратора: {order.admin_comment}"
        elif new_status == 'cancelled':
            title = "Заказ отменен"
            message = f"Ваш заказ товара «{order.product.name}» был отменен. Потраченные {order.points_spent} баллов возвращены на ваш счет."
            if order.admin_comment:
                message += f"\n\nКомментарий администратора: {order.admin_comment}"
        elif new_status == 'completed':
            title = "Заказ выполнен"
            message = f"Ваш заказ товара «{order.product.name}» выполнен. Вы можете получить товар."
        else:
            title = "Статус заказа изменен"
            message = f"Статус вашего заказа товара «{order.product.name}» изменен с «{old_status_display}» на «{new_status_display}»."
        
        return cls.objects.create(
            user=order.user,
            notification_type='order_status',
            title=title,
            message=message,
            related_order=order,
        )
    
    @classmethod
    def create_course_materials_updated_notification(cls, user, course, material_type, material_name):
        """
        Создает уведомление об обновлении материалов в завершенном курсе
        
        Args:
            user: Пользователь, которому отправляется уведомление
            course: Курс, в котором обновились материалы
            material_type: Тип материала ('lesson' или 'quiz')
            material_name: Название добавленного/обновленного материала
        """
        if material_type == 'lesson':
            title = "Новый урок в завершенном курсе"
            message = f"В курсе «{course.title}» добавлен новый урок «{material_name}»"
        elif material_type == 'quiz':
            title = "Новый тест в завершенном курсе"
            message = f"В курсе «{course.title}» добавлен новый тест «{material_name}»"
        elif material_type == 'lesson_updated':
            title = "Обновлен урок в завершенном курсе"
            message = f"В курсе «{course.title}» обновлен урок «{material_name}»"
        else:
            title = "Обновлены материалы в завершенном курсе"
            message = f"В курсе «{course.title}» обновлены материалы"
        
        return cls.objects.create(
            user=user,
            notification_type='course_materials_updated',
            title=title,
            message=message,
            related_course=course
        )
