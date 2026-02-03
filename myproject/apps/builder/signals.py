from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from .models import Incident
from myapp.models import UserCourse, QuizResult, UserAnswer
from quizzes.models import Question
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


def check_and_update_incident_studies_completed_status(incident):
    """
    Проверяет наличие неоцененных открытых ответов в тестах курса-инцидента
    и завершение обучения всеми назначенными пользователями.
    Обновляет статус инцидента на 'studies_completed', если:
    - есть неоцененные открытые ответы, или
    - все назначенные пользователи завершили обучение.
    """
    if not incident.course:
        return
    
    course = incident.course
    
    # Получаем всех назначенных пользователей инцидента
    assigned_users = incident.assigned_to.all()
    if not assigned_users.exists():
        return
    
    assigned_user_ids = list(assigned_users.values_list('id', flat=True))
    
    # Проверяем, все ли назначенные пользователи завершили курс
    completed_count = UserCourse.objects.filter(
        user_id__in=assigned_user_ids,
        course=course,
        status='completed'
    ).count()
    all_completed = completed_count == len(assigned_user_ids) and completed_count > 0
    
    # Проверяем, есть ли неоцененные открытые ответы для назначенных пользователей
    # в тестах курса-инцидента
    unrated_text_answers = UserAnswer.objects.filter(
        user_id__in=assigned_user_ids,
        quiz_result__course=course,
        question__question_type=Question.TEXT,
        is_correct__isnull=True,  # Не оценено
        answer_text__isnull=False,  # Есть текстовый ответ
        answer_text__gt=''  # Не пустой ответ
    ).exists()
    
    # Если статус уже 'resolved' или 'declined', не меняем его
    if incident.status in ['resolved', 'declined']:
        return
    
    # Если все пользователи завершили обучение, устанавливаем статус 'studies_completed'
    if all_completed:
        if incident.status != 'studies_completed':
            incident.status = 'studies_completed'
            incident.save(update_fields=['status', 'updated_at'])
            logger.info(f"Инцидент {incident.title} переведен в статус 'Обучение завершено' - все назначенные пользователи ({completed_count}) завершили обучение")
    # Если есть неоцененные открытые ответы, устанавливаем статус 'studies_completed'
    elif unrated_text_answers:
        if incident.status != 'studies_completed':
            incident.status = 'studies_completed'
            incident.save(update_fields=['status', 'updated_at'])
            logger.info(f"Инцидент {incident.title} переведен в статус 'Обучение завершено' - есть неоцененные открытые ответы в тестах")
    # Если нет неоцененных открытых ответов и не все завершили, и статус 'studies_completed', возвращаем к 'assigned'
    elif not unrated_text_answers and not all_completed and incident.status == 'studies_completed':
        incident.status = 'assigned'
        incident.save(update_fields=['status', 'updated_at'])
        logger.info(f"Инцидент {incident.title} возвращен в статус 'Назначен' - все открытые ответы оценены, но не все пользователи завершили обучение")


@receiver(post_save, sender=QuizResult)
def update_incident_status_on_quiz_result_change(sender, instance, created, **kwargs):
    """
    Обновляет статус инцидента при изменении результата теста.
    Проверяет наличие неоцененных открытых ответов.
    """
    if not instance.course or not instance.course.is_incident:
        return
    
    try:
        incidents = Incident.objects.filter(course=instance.course)
        for incident in incidents:
            check_and_update_incident_studies_completed_status(incident)
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса инцидента для результата теста {instance.id}: {e}")


@receiver(post_save, sender=UserAnswer)
def update_incident_status_on_user_answer_change(sender, instance, created, **kwargs):
    """
    Обновляет статус инцидента при изменении ответа пользователя.
    Проверяет наличие неоцененных открытых ответов.
    """
    if not instance.quiz_result or not instance.quiz_result.course:
        return
    
    course = instance.quiz_result.course
    if not course.is_incident:
        return
    
    try:
        incidents = Incident.objects.filter(course=course)
        for incident in incidents:
            check_and_update_incident_studies_completed_status(incident)
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса инцидента для ответа пользователя {instance.id}: {e}")

