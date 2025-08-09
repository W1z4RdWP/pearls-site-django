from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta

from .models import Notification


from users.models import Profile

# Словарь для хранения старых значений dascoin_points
_old_dascoin_values = {}

@receiver(pre_save, sender='users.Profile')
def store_old_dascoin_value(sender, instance, **kwargs):
    """Сохраняет старое значение dascoin_points перед сохранением"""
    try:
        old_instance = Profile.objects.get(pk=instance.pk)
        _old_dascoin_values[instance.pk] = old_instance.dascoin_points
    except Profile.DoesNotExist:
        _old_dascoin_values[instance.pk] = 0

@receiver(post_save, sender='users.Profile')
def create_dascoin_notification(sender, instance, created, **kwargs):
    """Создает уведомление при изменении баллов DASCOIN"""
    if not created:  # Только при обновлении профиля
        old_points = _old_dascoin_values.get(instance.pk, 0)
        new_points = instance.dascoin_points
        
        # Если баллы изменились
        if old_points != new_points:
            points_change = new_points - old_points
            # Получаем причину начисления из временного атрибута
            reason = getattr(instance, '_dascoin_reason', None)
            Notification.create_dascoin_notification(
                user=instance.user,
                points_change=points_change,
                reason=reason
            )
        
        # Очищаем сохраненное значение
        _old_dascoin_values.pop(instance.pk, None)





@receiver(post_save, sender='courses.UserCourseTrajectory')
def create_trajectory_assignment_notification_individual(sender, instance, created, **kwargs):
    """Создает уведомление при индивидуальном назначении траектории"""
    if created:
        Notification.create_trajectory_assignment_notification(instance.user, instance.trajectory)


def create_platform_update_notification_for_all(title, message):
    """Создает уведомление об обновлении платформы для всех пользователей"""
    users = User.objects.filter(is_active=True)
    for user in users:
        Notification.create_platform_update_notification(user, title, message)


@receiver(post_save, sender='myapp.ChangeLog')
def create_platform_update_notification_on_changelog(sender, instance, created, **kwargs):
    """Создает уведомление об обновлении платформы при создании новой записи в ChangeLog"""
    if created and instance.is_public:
        title = f"Обновление платформы до версии {instance.version}"
        message = f"{instance.title}\n\n{instance.description}"
        
        # Создаем уведомления для всех активных пользователей
        create_platform_update_notification_for_all(title, message)


def create_course_reminder_notifications():
    """Создает напоминания о курсах, которые были назначены автоматически"""
    # Находим курсы, назначенные через группы, но не пройденные
    from courses.models import UserCourse, Course
    
    # Получаем все курсы с автоматическим назначением
    auto_assigned_courses = Course.objects.filter(allowed_groups__isnull=False).distinct()
    
    for course in auto_assigned_courses:
        # Получаем пользователей, которым назначен курс через группы
        users_in_groups = User.objects.filter(
            groups__in=course.allowed_groups.all()
        ).distinct()
        
        for user in users_in_groups:
            # Проверяем, не проходил ли пользователь этот курс
            user_course, created = UserCourse.objects.get_or_create(
                user=user,
                course=course,
                defaults={'is_completed': False}
            )
            
            # Если курс не завершен и последнее напоминание было более 7 дней назад
            if not user_course.is_completed:
                last_reminder = Notification.objects.filter(
                    user=user,
                    notification_type='course_reminder',
                    related_course=course
                ).order_by('-created_at').first()
                
                if not last_reminder or (timezone.now() - last_reminder.created_at).days > 7:
                    Notification.create_course_reminder_notification(user, course)


def create_lesson_actualization_reminders():
    """Создает напоминания об актуализации уроков для ответственных"""
    from courses.models import Lesson
    
    # Здесь можно добавить логику для определения дат актуализации
    # Пока создаем заглушку
    lessons_needing_actualization = Lesson.objects.filter(
        # Добавить фильтры для уроков, требующих актуализации
        created_at__lt=timezone.now() - timedelta(days=365)  # Пример: уроки старше года
    )
    
    for lesson in lessons_needing_actualization:
        # Получаем ответственных пользователей (можно настроить по ролям)
        responsible_users = User.objects.filter(
            profile__role__isnull=False,
            is_staff=True
        )
        
        for user in responsible_users:
            # Проверяем, не было ли уже напоминания
            last_reminder = Notification.objects.filter(
                user=user,
                notification_type='lesson_actualization',
                related_lesson=lesson
            ).order_by('-created_at').first()
            
            if not last_reminder or (timezone.now() - last_reminder.created_at).days > 30:
                actualization_date = lesson.created_at + timedelta(days=365)  # Пример
                Notification.create_lesson_actualization_notification(
                    user, lesson, actualization_date
                )


# ==== уведомления для техподдержки ====
from django.db.models.signals import pre_save as model_pre_save
from tech_support.models import Ticket, TicketComment

# Храним старый статус по ticket.pk
_old_ticket_status = {}

@receiver(model_pre_save, sender=Ticket)
def store_old_ticket_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Ticket.objects.get(pk=instance.pk)
            _old_ticket_status[instance.pk] = old.status.name if old.status else None
        except Ticket.DoesNotExist:
            _old_ticket_status[instance.pk] = None
    else:
        _old_ticket_status[instance.pk] = None

@receiver(post_save, sender=Ticket)
def notify_ticket_status_change(sender, instance, created, **kwargs):
    if created:
        return
    old_name = _old_ticket_status.pop(instance.pk, None)
    new_name = instance.status.name if instance.status else None
    if old_name and new_name and old_name != new_name:
        # Кому слать: автор тикета и назначенный исполнитель (если есть и не равен автору)
        recipients = set()
        recipients.add(instance.created_by)
        if instance.assigned_to and instance.assigned_to != instance.created_by:
            recipients.add(instance.assigned_to)
        for user in recipients:
            Notification.create_ticket_status_notification(
                user=user,
                ticket=instance,
                old_status_name=old_name,
                new_status_name=new_name,
            )

@receiver(post_save, sender=TicketComment)
def notify_ticket_new_comment(sender, instance, created, **kwargs):
    if not created:
        return
    ticket = instance.ticket
    author = instance.author
    # Не уведомляем про внутренние комментарии
    if instance.is_internal:
        return
    # Кому слать: автор тикета, назначенный исполнитель; исключить автора комментария
    recipients = set()
    if ticket.created_by != author:
        recipients.add(ticket.created_by)
    if ticket.assigned_to and ticket.assigned_to != author:
        recipients.add(ticket.assigned_to)
    for user in recipients:
        Notification.create_ticket_comment_notification(
            user=user,
            ticket=ticket,
            author=author,
            comment_text=instance.content,
        ) 