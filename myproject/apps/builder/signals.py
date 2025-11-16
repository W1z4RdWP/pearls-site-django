from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Incident
from myapp.models import UserCourse
import logging

logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=Incident.assigned_to.through)
def update_course_access_on_incident_assignment_change(sender, instance, action, pk_set, **kwargs):
    """
    Сигнал для автоматического управления доступом к курсу при изменении назначенных пользователей инцидента.
    Работает как при редактировании через форму, так и через админ-панель.
    """
    if not instance.course:
        return
    
    course = instance.course
    
    if action == "post_remove":
        # При удалении пользователей из инцидента удаляем их доступ к курсу
        from django.contrib.auth import get_user_model
        User = get_user_model()
        removed_users = User.objects.filter(pk__in=pk_set)
        
        for user in removed_users:
            deleted_count, _ = UserCourse.objects.filter(user=user, course=course).delete()
            if deleted_count > 0:
                logger.info(f"Удален доступ к курсу {course.title} у пользователя {user.username} при удалении из инцидента {instance.title}")
    
    elif action == "post_add":
        # Автоназначение курса при добавлении пользователей в инцидент отключено
        # Назначение происходит вручную через кнопки в деталке курса
        pass

