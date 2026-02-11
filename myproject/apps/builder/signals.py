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
    Проверяет наличие неоцененных открытых ответов и результатов тестов в статусе pending
    в курсе-инциденте, а также завершение обучения всеми назначенными пользователями.

    - Если все назначенные завершили обучение и нет ожидающих проверки (ни открытых ответов,
      ни тестов/заданий в pending) — статус «Завершён» (resolved).
    - Если все завершили, но есть открытые ответы или тесты/задания в pending — статус
      «Обучение завершено» (studies_completed).
    """
    if not incident.course:
        return

    course = incident.course

    assigned_users = incident.assigned_to.all()
    if not assigned_users.exists():
        return

    assigned_user_ids = list(assigned_users.values_list('id', flat=True))

    completed_count = UserCourse.objects.filter(
        user_id__in=assigned_user_ids,
        course=course,
        status='completed'
    ).count()
    all_completed = completed_count == len(assigned_user_ids) and completed_count > 0

    # Неоцененные открытые ответы у назначенных в тестах курса-инцидента
    unrated_text_answers = UserAnswer.objects.filter(
        user_id__in=assigned_user_ids,
        quiz_result__course=course,
        question__question_type=Question.TEXT,
        is_correct__isnull=True,
        answer_text__isnull=False,
        answer_text__gt=''
    ).exists()

    # Результаты тестов в статусе pending (ожидают проверки наставника)
    pending_quiz_results = QuizResult.objects.filter(
        user_id__in=assigned_user_ids,
        course=course,
        status='pending'
    ).exists()

    needs_mentor_review = unrated_text_answers or pending_quiz_results

    if incident.status in ['resolved', 'declined']:
        return

    if all_completed:
        if not needs_mentor_review:
            if incident.status != 'resolved':
                incident.status = 'resolved'
                incident.save(update_fields=['status', 'updated_at'])
                logger.info(
                    f"Инцидент {incident.title} переведен в статус 'Завершён' - все назначенные ({completed_count}) "
                    "завершили обучение, ожидающих проверки нет"
                )
        else:
            if incident.status != 'studies_completed':
                incident.status = 'studies_completed'
                incident.save(update_fields=['status', 'updated_at'])
                logger.info(
                    f"Инцидент {incident.title} переведен в статус 'Обучение завершено' - все назначенные завершили "
                    "обучение, остались тесты/задания, ожидающие проверки наставника"
                )
    elif unrated_text_answers or pending_quiz_results:
        if incident.status != 'studies_completed':
            incident.status = 'studies_completed'
            incident.save(update_fields=['status', 'updated_at'])
            logger.info(
                f"Инцидент {incident.title} переведен в статус 'Обучение завершено' - есть неоцененные ответы "
                "или результаты в ожидании проверки"
            )
    elif incident.status == 'studies_completed':
        incident.status = 'assigned'
        incident.save(update_fields=['status', 'updated_at'])
        logger.info(
            f"Инцидент {incident.title} возвращен в статус 'Назначен' - открытые ответы оценены и нет pending, "
            "но не все пользователи завершили обучение"
        )


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

