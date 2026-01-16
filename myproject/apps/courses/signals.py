from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User,Group
from django.utils import timezone
from datetime import timedelta
from courses.models import Course, Trajectory, UserCourseTrajectory, TrajectoryCourse, ManualTrajectoryUnassignment, Lesson
from quizzes.models import Quiz, Homework
from myapp.models import UserCourse, ManualCourseUnassignment
from user_management.utils import send_course_assignment_email, send_trajectory_assignment_email
import logging

logger = logging.getLogger(__name__)

# Словарь для хранения старых значений UserCourse перед сохранением
_user_course_old_status = {}

# Словари для хранения предыдущих связей уроков, тестов и заданий с курсами
# Ключ: ID урока/теста/задания, значение: set() с ID курсов
_lesson_courses_before_save = {}
_quiz_courses_before_save = {}
_homework_courses_before_save = {}




@receiver(m2m_changed, sender=User.groups.through)
def assign_courses_on_group_add(sender, instance, action, pk_set, **kwargs):
    logger.info(f"Сигнал assign_courses_on_group_add: action={action}, user={instance.username}")
    
    if action == "post_add":
        # Для новых групп пользователя
        user_groups = instance.groups.filter(pk__in=pk_set)
        
        # Найти курсы, доступные для этих групп
        courses = Course.objects.filter(allowed_groups__in=user_groups).distinct()
        
        # Создать UserCourse для каждого подходящего курса
        for course in courses:
            # Проверяем, не был ли курс отменен вручную
            manual_unassignment = ManualCourseUnassignment.objects.filter(
                user=instance, 
                course=course
            ).first()
            
            if manual_unassignment:
                logger.info(
                    f"Пропуск автоматического назначения курса {course.title} пользователю {instance.username}: "
                    f"курс был отменен вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                    f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
                )
                continue
            
            user_course, created = UserCourse.objects.get_or_create(user=instance, course=course)
            if created:
                logger.info(f"Назначен курс {course.title} пользователю {instance.username}")
                # Создаем внутреннее уведомление
                try:
                    from notifications.models import Notification
                    Notification.create_course_assignment_notification(instance, course)
                except Exception as e:
                    logger.error(f"Ошибка создания внутреннего уведомления о курсе {course.title}: {e}")
                
                # Отправляем email уведомление
                try:
                    send_course_assignment_email(instance, course)
                    logger.info(f"Отправлено email уведомление о курсе {course.title} пользователю {instance.email}")
                except Exception as e:
                    logger.error(f"Ошибка отправки email уведомления о курсе {course.title}: {e}")
    elif action == "post_remove":
        # При удалении пользователя из группы
        removed_groups = Group.objects.filter(pk__in=pk_set)
        
        # Удаляем курсы, которые больше не доступны
        for group in removed_groups:
            courses_to_remove = Course.objects.filter(allowed_groups=group)
            for course in courses_to_remove:
                # Проверяем, есть ли у пользователя другие группы с доступом к этому курсу
                user_has_access = Course.objects.filter(
                    allowed_groups__in=instance.groups.all()
                ).filter(id=course.id).exists()
                if not user_has_access:
                    UserCourse.objects.filter(user=instance, course=course).delete()
                    logger.info(f"Удален курс {course.title} у пользователя {instance.username}")




@receiver(m2m_changed, sender=Course.allowed_groups.through)
def assign_courses_on_course_update(sender, instance, action, pk_set, **kwargs):
    logger.info(f"Сигнал assign_courses_on_course_update: action={action}, course={instance.title}")
    
    if action == "post_add":
        # Для новых групп курса
        groups = instance.allowed_groups.filter(pk__in=pk_set)
        
        # Найти пользователей в этих группах
        users = User.objects.filter(groups__in=groups).distinct()
        
        # Назначить курс пользователям
        for user in users:
            # Проверяем, не был ли курс отменен вручную
            manual_unassignment = ManualCourseUnassignment.objects.filter(
                user=user, 
                course=instance
            ).first()
            
            if manual_unassignment:
                logger.info(
                    f"Пропуск автоматического назначения курса {instance.title} пользователю {user.username}: "
                    f"курс был отменен вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                    f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
                )
                continue
            
            user_course, created = UserCourse.objects.get_or_create(user=user, course=instance)
            if created:
                logger.info(f"Назначен курс {instance.title} пользователю {user.username}")
                # Создаем внутреннее уведомление
                try:
                    from notifications.models import Notification
                    Notification.create_course_assignment_notification(user, instance)
                except Exception as e:
                    logger.error(f"Ошибка создания внутреннего уведомления о курсе {instance.title}: {e}")
                
                # Отправляем email уведомление
                try:
                    send_course_assignment_email(user, instance)
                    logger.info(f"Отправлено email уведомление о курсе {instance.title} пользователю {user.email}")
                except Exception as e:
                    logger.error(f"Ошибка отправки email уведомления о курсе {instance.title}: {e}")




@receiver(m2m_changed, sender=User.groups.through)
def assign_trajectories_on_group_add(sender, instance, action, pk_set, **kwargs):
    logger.info(f"Сигнал assign_trajectories_on_group_add: action={action}, user={instance.username}")
    
    if action == "post_add":
        user_groups = instance.groups.filter(pk__in=pk_set)
        trajectories = Trajectory.objects.filter(groups__in=user_groups).distinct()
        for trajectory in trajectories:
            # Проверяем, не была ли траектория отменена вручную
            manual_unassignment = ManualTrajectoryUnassignment.objects.filter(
                user=instance, 
                trajectory=trajectory
            ).first()
            
            if manual_unassignment:
                logger.info(
                    f"Пропуск автоматического назначения траектории {trajectory.name} пользователю {instance.username}: "
                    f"траектория была отменена вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                    f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
                )
                continue
            
            user_trajectory, created = UserCourseTrajectory.objects.get_or_create(user=instance, trajectory=trajectory)
            # Если траектория только что создана, назначаем курсы из неё
            if created:
                logger.info(f"Назначена траектория {trajectory.name} пользователю {instance.username}")
                # Назначаем курсы БЕЗ отправки email уведомлений о курсах и БЕЗ создания внутренних уведомлений
                assign_courses_from_trajectory(instance, trajectory, send_email_notifications=False, create_notifications=False)
                
                # Создаем внутреннее уведомление о траектории
                try:
                    from notifications.models import Notification
                    Notification.create_trajectory_assignment_notification(instance, trajectory)
                except Exception as e:
                    logger.error(f"Ошибка создания внутреннего уведомления о траектории {trajectory.name}: {e}")
                
                # Отправляем ТОЛЬКО одно email уведомление о траектории
                try:
                    send_trajectory_assignment_email(instance, trajectory)
                    logger.info(f"Отправлено email уведомление о траектории {trajectory.name} пользователю {instance.email}")
                except Exception as e:
                    logger.error(f"Ошибка отправки email уведомления о траектории {trajectory.name}: {e}")
    elif action == "post_remove":
        # При удалении пользователя из группы
        removed_groups = Group.objects.filter(pk__in=pk_set)
        
        # Удаляем траектории, которые больше не доступны
        for group in removed_groups:
            trajectories_to_remove = Trajectory.objects.filter(groups=group)
            for trajectory in trajectories_to_remove:
                # Проверяем, есть ли у пользователя другие группы с доступом к этой траектории
                user_has_access = Trajectory.objects.filter(
                    groups__in=instance.groups.all()
                ).filter(id=trajectory.id).exists()
                if not user_has_access:
                    # Удаляем траекторию и связанные курсы
                    user_trajectory = UserCourseTrajectory.objects.filter(user=instance, trajectory=trajectory).first()
                    if user_trajectory:
                        # Удаляем курсы из этой траектории
                        trajectory_courses = TrajectoryCourse.objects.filter(trajectory=trajectory)
                        for tc in trajectory_courses:
                            UserCourse.objects.filter(user=instance, course=tc.course).delete()
                        # Удаляем саму траекторию
                        user_trajectory.delete()
                        logger.info(f"Удалена траектория {trajectory.name} у пользователя {instance.username}")




@receiver(m2m_changed, sender=Trajectory.groups.through)
def assign_trajectories_on_trajectory_update(sender, instance, action, pk_set, **kwargs):
    logger.info(f"Сигнал assign_trajectories_on_trajectory_update: action={action}, trajectory={instance.name}")
    
    if action == "post_add":
        # Для новых групп траектории
        groups = instance.groups.filter(pk__in=pk_set)
        
        # Найти пользователей в этих группах
        users = User.objects.filter(groups__in=groups).distinct()
        
        # Назначить траекторию пользователям
        for user in users:
            # Проверяем, не была ли траектория отменена вручную
            manual_unassignment = ManualTrajectoryUnassignment.objects.filter(
                user=user, 
                trajectory=instance
            ).first()
            
            if manual_unassignment:
                logger.info(
                    f"Пропуск автоматического назначения траектории {instance.name} пользователю {user.username}: "
                    f"траектория была отменена вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                    f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
                )
                continue
            
            user_trajectory, created = UserCourseTrajectory.objects.get_or_create(user=user, trajectory=instance)
            # Если траектория только что создана, назначаем курсы из неё
            if created:
                logger.info(f"Назначена траектория {instance.name} пользователю {user.username}")
                # Назначаем курсы БЕЗ отправки email уведомлений о курсах и БЕЗ создания внутренних уведомлений
                assign_courses_from_trajectory(user, instance, send_email_notifications=False, create_notifications=False)
                
                # Создаем внутреннее уведомление о траектории
                try:
                    from notifications.models import Notification
                    Notification.create_trajectory_assignment_notification(user, instance)
                except Exception as e:
                    logger.error(f"Ошибка создания внутреннего уведомления о траектории {instance.name}: {e}")
                
                # Отправляем ТОЛЬКО одно email уведомление о траектории
                try:
                    send_trajectory_assignment_email(user, instance)
                    logger.info(f"Отправлено email уведомление о траектории {instance.name} пользователю {user.email}")
                except Exception as e:
                    logger.error(f"Ошибка отправки email уведомления о траектории {instance.name}: {e}")




@receiver(post_save, sender=TrajectoryCourse)
def assign_course_to_trajectory_users(sender, instance, created, **kwargs):
    """
    При добавлении курса в траекторию, назначаем его всем пользователям этой траектории
    """

    if created:
        logger.info(f"Сигнал assign_course_to_trajectory_users: добавлен курс {instance.course.title} в траекторию {instance.trajectory.name}")
        
        # Получаем всех пользователей, у которых есть эта траектория
        user_trajectories = UserCourseTrajectory.objects.filter(trajectory=instance.trajectory)
        
        for user_trajectory in user_trajectories:
            # Проверяем, не был ли курс отменен вручную
            manual_unassignment = ManualCourseUnassignment.objects.filter(
                user=user_trajectory.user, 
                course=instance.course
            ).first()
            
            if manual_unassignment:
                logger.info(
                    f"Пропуск автоматического назначения курса {instance.course.title} пользователю {user_trajectory.user.username}: "
                    f"курс был отменен вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                    f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
                )
                continue
            
            user_course, course_created = UserCourse.objects.get_or_create(
                user=user_trajectory.user,
                course=instance.course,
                defaults={'status': 'available'}
            )
            if course_created:
                logger.info(f"Назначен курс {instance.course.title} пользователю {user_trajectory.user.username}")
                # НЕ отправляем email уведомление, так как курс является частью траектории
                # Пользователь уже получил уведомление о назначении траектории




def assign_courses_from_trajectory(user, trajectory, send_email_notifications=False, create_notifications=False):
    """
    Назначает пользователю курсы из траектории в правильном порядке
    
    Args:
        user: Пользователь
        trajectory: Траектория
        send_email_notifications: Отправлять ли email уведомления для каждого курса (по умолчанию False)
        create_notifications: Создавать ли внутренние уведомления для каждого курса (по умолчанию False)
    """

    logger.info(f"Назначаем курсы из траектории {trajectory.name} пользователю {user.username}")
    
    trajectory_courses = TrajectoryCourse.objects.filter(trajectory=trajectory).order_by('order')
    
    for tc in trajectory_courses:
        # Проверяем, не был ли курс отменен вручную
        manual_unassignment = ManualCourseUnassignment.objects.filter(
            user=user, 
            course=tc.course
        ).first()
        
        if manual_unassignment:
            logger.info(
                f"Пропуск автоматического назначения курса {tc.course.title} пользователю {user.username}: "
                f"курс был отменен вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
            )
            continue
        
        user_course, created = UserCourse.objects.get_or_create(
            user=user,
            course=tc.course,
            defaults={'status': 'available'}
        )
        if created:
            logger.info(f"Назначен курс {tc.course.title} пользователю {user.username}")
            
            # Создаем внутреннее уведомление только если это явно запрошено
            if create_notifications:
                try:
                    from notifications.models import Notification
                    Notification.create_course_assignment_notification(user, tc.course)
                except Exception as e:
                    logger.error(f"Ошибка создания внутреннего уведомления о курсе {tc.course.title}: {e}")
            
            # Отправляем email уведомление только если это явно запрошено
            if send_email_notifications:
                try:
                    send_course_assignment_email(user, tc.course)
                    logger.info(f"Отправлено email уведомление о курсе {tc.course.title} пользователю {user.email}")
                except Exception as e:
                    logger.error(f"Ошибка отправки email уведомления о курсе {tc.course.title}: {e}")


@receiver(post_save, sender=UserCourse)
def auto_assign_specialized_courses_on_completion(sender, instance, created, **kwargs):
    """
    Автоматически выдает доступ к специализированным курсам/траекториям 
    для медсестер/ассистентов после завершения курса "Внедрение м/с и асс. День 6."
    """
    # Проверяем, что курс завершен и это не создание новой записи
    if instance.status == 'completed' and not created:
        user = instance.user
        course = instance.course
        
        # Проверяем, что это курс "Внедрение м/с и асс. День 6."
        if "Внедрение м/с и асс. День 6" in course.title or "Внедрение м/с и асс. День 6." in course.title:
            logger.info(f"Пользователь {user.username} завершил курс {course.title}")
            
            # Получаем группы пользователя
            user_groups = user.groups.all()
            
            # Проверяем, состоит ли пользователь в группе "Медсестра/ассистент"
            nurse_assistant_group = Group.objects.filter(name="Медсестра/ассистент").first()
            if not nurse_assistant_group or nurse_assistant_group not in user_groups:
                logger.info(f"Пользователь {user.username} не состоит в группе 'Медсестра/ассистент'")
                return
            
            # Специализированные группы для медсестер/ассистентов
            specialized_groups = [
                "Медицинская сестра/ассистент в хирургии",
                "Медицинская сестра/ассистент в терапии", 
                "Медицинская сестра/ассистент в ортопедии",
                "Медицинская сестра/ассистент в ортодонтии"
            ]
            
            # Проверяем, состоит ли пользователь в какой-либо из специализированных групп
            user_specialized_groups = user_groups.filter(name__in=specialized_groups)
            
            if user_specialized_groups.exists():
                logger.info(f"Пользователь {user.username} состоит в специализированных группах: {[g.name for g in user_specialized_groups]}")
                
                # Находим курсы и траектории, доступные для этих специализированных групп
                specialized_courses = Course.objects.filter(
                    allowed_groups__in=user_specialized_groups
                ).distinct()
                
                specialized_trajectories = Trajectory.objects.filter(
                    groups__in=user_specialized_groups
                ).distinct()
                
                # Назначаем курсы
                for course in specialized_courses:
                    # Проверяем, не был ли курс отменен вручную
                    manual_unassignment = ManualCourseUnassignment.objects.filter(
                        user=user, 
                        course=course
                    ).first()
                    
                    if manual_unassignment:
                        logger.info(
                            f"Пропуск автоматического назначения специализированного курса {course.title} пользователю {user.username}: "
                            f"курс был отменен вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                            f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
                        )
                        continue
                    
                    user_course, created = UserCourse.objects.get_or_create(
                        user=user,
                        course=course,
                        defaults={'status': 'available'}
                    )
                    if created:
                        logger.info(f"Назначен специализированный курс {course.title} пользователю {user.username}")
                        
                        # Создаем внутреннее уведомление
                        try:
                            from notifications.models import Notification
                            Notification.create_course_assignment_notification(user, course)
                        except Exception as e:
                            logger.error(f"Ошибка создания уведомления о курсе {course.title}: {e}")
                        
                        # Отправляем email уведомление
                        try:
                            send_course_assignment_email(user, course)
                            logger.info(f"Отправлено email уведомление о курсе {course.title} пользователю {user.email}")
                        except Exception as e:
                            logger.error(f"Ошибка отправки email уведомления о курсе {course.title}: {e}")
                
                # Назначаем траектории
                for trajectory in specialized_trajectories:
                    # Проверяем, не была ли траектория отменена вручную
                    manual_unassignment = ManualTrajectoryUnassignment.objects.filter(
                        user=user, 
                        trajectory=trajectory
                    ).first()
                    
                    if manual_unassignment:
                        logger.info(
                            f"Пропуск автоматического назначения специализированной траектории {trajectory.name} пользователю {user.username}: "
                            f"траектория была отменена вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                            f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
                        )
                        continue
                    
                    user_trajectory, created = UserCourseTrajectory.objects.get_or_create(
                        user=user,
                        trajectory=trajectory
                    )
                    if created:
                        logger.info(f"Назначена специализированная траектория {trajectory.name} пользователю {user.username}")
                        
                        # Назначаем курсы из траектории
                        assign_courses_from_trajectory(user, trajectory, send_email_notifications=False, create_notifications=False)
                        
                        # Создаем внутреннее уведомление о траектории
                        try:
                            from notifications.models import Notification
                            Notification.create_trajectory_assignment_notification(user, trajectory)
                        except Exception as e:
                            logger.error(f"Ошибка создания уведомления о траектории {trajectory.name}: {e}")
                        
                        # Отправляем email уведомление о траектории
                        try:
                            send_trajectory_assignment_email(user, trajectory)
                            logger.info(f"Отправлено email уведомление о траектории {trajectory.name} пользователю {user.email}")
                        except Exception as e:
                            logger.error(f"Ошибка отправки email уведомления о траектории {trajectory.name}: {e}")
            else:
                logger.info(f"Пользователь {user.username} не состоит ни в одной специализированной группе")


@receiver(pre_save, sender=UserCourse)
def store_old_user_course_status(sender, instance, **kwargs):
    """
    Сохраняем старый статус UserCourse перед сохранением для проверки изменений
    """
    if instance.pk:
        try:
            old_instance = UserCourse.objects.get(pk=instance.pk)
            _user_course_old_status[instance.pk] = old_instance.status
        except UserCourse.DoesNotExist:
            _user_course_old_status[instance.pk] = None
    else:
        # Для новых записей используем временный ключ
        _user_course_old_status[id(instance)] = None


@receiver(post_save, sender=UserCourse)
def set_default_deadline_for_usercourse(sender, instance, created, **kwargs):
    """
    Автоматически устанавливает deadline на основе course.default_deadline_days,
    если deadline не установлен и у курса есть default_deadline_days.
    Этот сигнал работает как резервный механизм, если deadline не был установлен в методе save().
    """
    # Устанавливаем deadline только если он не установлен и курс имеет default_deadline_days
    if not instance.deadline and instance.course_id:
        # Перезагружаем курс, чтобы получить актуальное значение default_deadline_days
        try:
            course = Course.objects.get(pk=instance.course_id)
            if course.default_deadline_days and course.default_deadline_days > 0:
                deadline = timezone.now() + timedelta(days=course.default_deadline_days)
                # Используем update() чтобы избежать повторного вызова save() и сигналов
                UserCourse.objects.filter(pk=instance.pk, deadline__isnull=True).update(deadline=deadline)
        except Course.DoesNotExist:
            pass


@receiver(post_save, sender=UserCourse)
def check_incident_completion_on_course_completion(sender, instance, created, **kwargs):
    """
    Проверяет, все ли назначенные пользователи завершили курс-инцидент,
    и если да, меняет статус инцидента на 'Завершён'
    """
    # Проверяем, что курс завершен и статус изменился на 'completed'
    if instance.status == 'completed':
        # Получаем старый статус
        if instance.pk:
            old_status = _user_course_old_status.pop(instance.pk, None)
        else:
            # Для новых записей используем временный ключ
            old_status = _user_course_old_status.pop(id(instance), None)
        
        # Если статус изменился на 'completed' (не был 'completed' ранее) или это новая запись
        if old_status != 'completed' or created:
            course = instance.course
            
            # Проверяем, что курс является инцидентом
            if course and course.is_incident:
                try:
                    from builder.models import Incident
                    
                    # Находим все инциденты, связанные с этим курсом
                    incidents = Incident.objects.filter(course=course)
                    
                    for incident in incidents:
                        user = instance.user
                        
                        # Получаем всех назначенных пользователей инцидента (кэшируем для использования в двух местах)
                        assigned_users = incident.assigned_to.all()
                        
                        # Проверяем, является ли пользователь, завершивший курс, expert для инцидента
                        if incident.expert and incident.expert == user:
                            # Expert завершил курс - назначаем курс всем пользователям из assigned_to
                            if assigned_users.exists():
                                # Определяем дедлайн: приоритет у course.default_deadline_days, иначе используем incident.assigned_to_time_to_complete
                                if course.default_deadline_days and course.default_deadline_days > 0:
                                    deadline = timezone.now() + timedelta(days=course.default_deadline_days)
                                else:
                                    # Получаем время на завершение из инцидента (по умолчанию 3 дня)
                                    time_to_complete = incident.assigned_to_time_to_complete or 3
                                    deadline = timezone.now() + timedelta(days=time_to_complete)
                                
                                assigned_count = 0
                                for assigned_user in assigned_users:
                                    # Проверяем, не был ли курс отменен вручную
                                    manual_unassignment = ManualCourseUnassignment.objects.filter(
                                        user=assigned_user, 
                                        course=course
                                    ).first()
                                    
                                    if manual_unassignment:
                                        logger.info(
                                            f"Пропуск автоматического назначения курса-инцидента {course.title} пользователю {assigned_user.username}: "
                                            f"курс был отменен вручную {manual_unassignment.unassigned_at.strftime('%d.%m.%Y')} "
                                            f"пользователем {manual_unassignment.unassigned_by.username if manual_unassignment.unassigned_by else 'неизвестно'}"
                                        )
                                        continue
                                    
                                    # Проверяем, не назначен ли уже курс пользователю
                                    user_course, created = UserCourse.objects.get_or_create(
                                        user=assigned_user,
                                        course=course,
                                        defaults={
                                            'status': 'available',
                                            'deadline': deadline
                                        }
                                    )
                                    
                                    # Если курс уже был назначен, обновляем deadline только если он не был установлен ранее
                                    if not created and not user_course.deadline:
                                        user_course.deadline = deadline
                                        user_course.save(update_fields=['deadline'])
                                    
                                    if created:
                                        assigned_count += 1
                                        # Создаем внутреннее уведомление
                                        try:
                                            from notifications.models import Notification
                                            Notification.create_course_assignment_notification(assigned_user, course)
                                        except Exception as e:
                                            logger.error(f"Ошибка создания внутреннего уведомления о курсе-инциденте {course.title}: {e}")
                                        
                                        # Отправляем email уведомление
                                        try:
                                            send_course_assignment_email(assigned_user, course)
                                            logger.info(f"Отправлено email уведомление о курсе-инциденте {course.title} пользователю {assigned_user.email}")
                                        except Exception as e:
                                            logger.error(f"Ошибка отправки email уведомления о курсе-инциденте {course.title}: {e}")
                                
                                logger.info(f"После завершения курса expert'ом ({user.username}) курс {course.title} автоматически назначен {assigned_count} пользователям из assigned_to инцидента {incident.title}")
                        
                        if not assigned_users.exists():
                            # Если нет назначенных пользователей, пропускаем
                            continue
                        
                        # Проверяем, все ли назначенные пользователи завершили курс
                        # Оптимизация: используем один запрос вместо цикла
                        assigned_user_ids = list(assigned_users.values_list('id', flat=True))
                        completed_count = UserCourse.objects.filter(
                            user_id__in=assigned_user_ids,
                            course=course,
                            status='completed'
                        ).count()
                        
                        # Если все назначенные пользователи завершили курс
                        if completed_count == len(assigned_user_ids) and incident.status != 'resolved':
                            incident.status = 'resolved'
                            if not incident.resolved_at:
                                incident.resolved_at = timezone.now()
                            incident.save(update_fields=['status', 'resolved_at', 'updated_at'])
                            logger.info(f"Инцидент {incident.title} автоматически завершен, так как все назначенные пользователи ({completed_count}) завершили курс")
                
                except ImportError:
                    # Если модель Incident не найдена, просто пропускаем
                    pass
                except Exception as e:
                    logger.error(f"Ошибка при проверке завершения инцидента для курса {course.title}: {e}")


def notify_completed_course_users_about_material_update(course, material_type, material_name):
    """
    Отправляет уведомления всем пользователям, которые уже завершили курс,
    о добавлении нового материала (урока или теста) или обновлении урока.
    
    Args:
        course: Курс, в котором обновились материалы
        material_type: Тип материала ('lesson', 'quiz', или 'lesson_updated')
        material_name: Название добавленного/обновленного материала
    """
    try:
        from notifications.models import Notification
        from django.utils import timezone
        from datetime import timedelta
        
        # Находим всех пользователей, которые завершили этот курс
        completed_user_courses = UserCourse.objects.filter(
            course=course,
            status='completed'
        ).select_related('user')
        
        # Время для проверки дубликатов (последние 5 минут)
        time_threshold = timezone.now() - timedelta(minutes=5)
        
        notification_count = 0
        for user_course in completed_user_courses:
            try:
                # Проверяем, не было ли уже отправлено похожее уведомление в последние 5 минут
                # Это защита от дубликатов при одновременных операциях
                recent_notification = Notification.objects.filter(
                    user=user_course.user,
                    related_course=course,
                    notification_type='course_materials_updated',
                    created_at__gte=time_threshold
                ).first()
                
                # Если есть недавнее уведомление для этого курса, пропускаем
                if recent_notification:
                    logger.debug(
                        f"Пропуск дубликата уведомления для пользователя {user_course.user.username} "
                        f"о курсе {course.title} (уже есть уведомление от {recent_notification.created_at})"
                    )
                    continue
                
                Notification.create_course_materials_updated_notification(
                    user=user_course.user,
                    course=course,
                    material_type=material_type,
                    material_name=material_name
                )
                notification_count += 1
            except Exception as e:
                logger.error(
                    f"Ошибка создания уведомления для пользователя {user_course.user.username} "
                    f"о обновлении материалов в курсе {course.title}: {e}"
                )
        
        if notification_count > 0:
            logger.info(
                f"Отправлено {notification_count} уведомлений пользователям с завершенным курсом "
                f"«{course.title}» о добавлении/обновлении материала: {material_name}"
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений о обновлении материалов курса {course.title}: {e}")


@receiver(m2m_changed, sender=Lesson.courses.through)
def track_lesson_courses_before_change(sender, instance, action, pk_set, **kwargs):
    """
    Сохраняет текущие связи урока с курсами перед изменением.
    Это необходимо для определения, действительно ли курс был добавлен,
    а не просто пересохранен через форму.
    
    Логика:
    - При использовании .set() Django вызывает pre_clear (связи еще есть) -> сохраняем
    - При использовании только .add() Django вызывает pre_add (связи еще есть) -> сохраняем
    """
    lesson_id = instance.pk
    if not lesson_id:
        return
    
    if action == "pre_clear":
        # Сохраняем текущие связи перед очисткой (они еще есть)
        _lesson_courses_before_save[lesson_id] = set(
            instance.courses.values_list('pk', flat=True)
        )
    elif action == "pre_add":
        # Сохраняем текущие связи только если они еще не были сохранены
        # (т.е. если pre_clear не был вызван, значит используется только .add())
        if lesson_id not in _lesson_courses_before_save:
            _lesson_courses_before_save[lesson_id] = set(
                instance.courses.values_list('pk', flat=True)
            )


@receiver(m2m_changed, sender=Lesson.courses.through)
def notify_on_lesson_added_to_course(sender, instance, action, pk_set, **kwargs):
    """
    Отслеживает добавление урока к курсу и отправляет уведомления
    пользователям, которые уже завершили этот курс.
    
    Важно: сигнал срабатывает только при реальном добавлении урока к новому курсу.
    Проверяет, что курс не был связан с уроком до этой операции.
    """
    if action == "post_add" and pk_set:
        lesson_id = instance.pk
        if not lesson_id:
            return
        
        # Получаем предыдущие связи (если они были сохранены)
        previous_courses = _lesson_courses_before_save.get(lesson_id, set())
        
        # Получаем курсы, к которым был добавлен урок (только те, что в pk_set)
        courses = Course.objects.filter(pk__in=pk_set)
        
        for course in courses:
            # Дополнительная проверка: убеждаемся, что курс действительно в списке курсов урока
            # Это защита от возможных race conditions
            if course not in instance.courses.all():
                continue
            
            # КЛЮЧЕВАЯ ПРОВЕРКА: курс должен быть новым (не был в предыдущих связях)
            if course.pk in previous_courses:
                logger.debug(
                    f"Пропуск уведомления: урок «{instance.title}» уже был связан с курсом «{course.title}» "
                    f"(это пересохранение формы, а не реальное добавление)"
                )
                continue
            
            logger.info(
                f"Урок «{instance.title}» добавлен к курсу «{course.title}»"
            )
            # Отправляем уведомления пользователям с завершенным курсом
            notify_completed_course_users_about_material_update(
                course=course,
                material_type='lesson',
                material_name=instance.title
            )
        
        # Очищаем сохраненное состояние после обработки
        _lesson_courses_before_save.pop(lesson_id, None)


@receiver(m2m_changed, sender=Quiz.courses.through)
def track_quiz_courses_before_change(sender, instance, action, pk_set, **kwargs):
    """
    Сохраняет текущие связи теста с курсами перед изменением.
    Это необходимо для определения, действительно ли курс был добавлен,
    а не просто пересохранен через форму.
    
    Логика:
    - При использовании .set() Django вызывает pre_clear (связи еще есть) -> сохраняем
    - При использовании только .add() Django вызывает pre_add (связи еще есть) -> сохраняем
    """
    quiz_id = instance.pk
    if not quiz_id:
        return
    
    if action == "pre_clear":
        # Сохраняем текущие связи перед очисткой (они еще есть)
        _quiz_courses_before_save[quiz_id] = set(
            instance.courses.values_list('pk', flat=True)
        )
    elif action == "pre_add":
        # Сохраняем текущие связи только если они еще не были сохранены
        # (т.е. если pre_clear не был вызван, значит используется только .add())
        if quiz_id not in _quiz_courses_before_save:
            _quiz_courses_before_save[quiz_id] = set(
                instance.courses.values_list('pk', flat=True)
            )


@receiver(m2m_changed, sender=Quiz.courses.through)
def notify_on_quiz_added_to_course(sender, instance, action, pk_set, **kwargs):
    """
    Отслеживает добавление теста к курсу и отправляет уведомления
    пользователям, которые уже завершили этот курс.
    
    Важно: сигнал срабатывает только при реальном добавлении теста к новому курсу.
    Проверяет, что курс не был связан с тестом до этой операции.
    """
    if action == "post_add" and pk_set:
        quiz_id = instance.pk
        if not quiz_id:
            return
        
        # Получаем предыдущие связи (если они были сохранены)
        previous_courses = _quiz_courses_before_save.get(quiz_id, set())
        
        # Получаем курсы, к которым был добавлен тест (только те, что в pk_set)
        courses = Course.objects.filter(pk__in=pk_set)
        
        for course in courses:
            # Дополнительная проверка: убеждаемся, что курс действительно в списке курсов теста
            # Это защита от возможных race conditions
            if course not in instance.courses.all():
                continue
            
            # КЛЮЧЕВАЯ ПРОВЕРКА: курс должен быть новым (не был в предыдущих связях)
            if course.pk in previous_courses:
                logger.debug(
                    f"Пропуск уведомления: тест «{instance.name}» уже был связан с курсом «{course.title}» "
                    f"(это пересохранение формы, а не реальное добавление)"
                )
                continue
            
            logger.info(
                f"Тест «{instance.name}» добавлен к курсу «{course.title}»"
            )
            # Отправляем уведомления пользователям с завершенным курсом
            notify_completed_course_users_about_material_update(
                course=course,
                material_type='quiz',
                material_name=instance.name
            )
        
        # Очищаем сохраненное состояние после обработки
        _quiz_courses_before_save.pop(quiz_id, None)


@receiver(m2m_changed, sender=Homework.courses.through)
def track_homework_courses_before_change(sender, instance, action, pk_set, **kwargs):
    """
    Сохраняет текущие связи задания с курсами перед изменением.
    Это необходимо для определения, действительно ли курс был добавлен,
    а не просто пересохранен через форму.
    
    Логика:
    - При использовании .set() Django вызывает pre_clear (связи еще есть) -> сохраняем
    - При использовании только .add() Django вызывает pre_add (связи еще есть) -> сохраняем
    """
    homework_id = instance.pk
    if not homework_id:
        return
    
    if action == "pre_clear":
        # Сохраняем текущие связи перед очисткой (они еще есть)
        _homework_courses_before_save[homework_id] = set(
            instance.courses.values_list('pk', flat=True)
        )
    elif action == "pre_add":
        # Сохраняем текущие связи только если они еще не были сохранены
        # (т.е. если pre_clear не был вызван, значит используется только .add())
        if homework_id not in _homework_courses_before_save:
            _homework_courses_before_save[homework_id] = set(
                instance.courses.values_list('pk', flat=True)
            )


@receiver(m2m_changed, sender=Homework.courses.through)
def notify_on_homework_added_to_course(sender, instance, action, pk_set, **kwargs):
    """
    Отслеживает добавление задания к курсу и отправляет уведомления
    пользователям, которые уже завершили этот курс.
    
    Важно: сигнал срабатывает только при реальном добавлении задания к новому курсу.
    Проверяет, что курс не был связан с заданием до этой операции.
    
    Использует тот же тип уведомления, что и для тестов (material_type='quiz'),
    как было запрошено пользователем.
    """
    if action == "post_add" and pk_set:
        homework_id = instance.pk
        if not homework_id:
            return
        
        # Получаем предыдущие связи (если они были сохранены)
        previous_courses = _homework_courses_before_save.get(homework_id, set())
        
        # Получаем курсы, к которым было добавлено задание (только те, что в pk_set)
        courses = Course.objects.filter(pk__in=pk_set)
        
        for course in courses:
            # Дополнительная проверка: убеждаемся, что курс действительно в списке курсов задания
            # Это защита от возможных race conditions
            if course not in instance.courses.all():
                continue
            
            # КЛЮЧЕВАЯ ПРОВЕРКА: курс должен быть новым (не был в предыдущих связях)
            if course.pk in previous_courses:
                logger.debug(
                    f"Пропуск уведомления: задание «{instance.name}» уже было связано с курсом «{course.title}» "
                    f"(это пересохранение формы, а не реальное добавление)"
                )
                continue
            
            logger.info(
                f"Задание «{instance.name}» добавлено к курсу «{course.title}»"
            )
            # Отправляем уведомления пользователям с завершенным курсом
            # Используем material_type='quiz', как было запрошено пользователем
            notify_completed_course_users_about_material_update(
                course=course,
                material_type='quiz',
                material_name=instance.name
            )
        
        # Очищаем сохраненное состояние после обработки
        _homework_courses_before_save.pop(homework_id, None)


# Удален сигнал post_save для Lesson, так как обновление урока само по себе
# не должно вызывать уведомления. Уведомления отправляются только при добавлении
# нового материала (урока, теста или задания) к курсу через сигналы m2m_changed.
