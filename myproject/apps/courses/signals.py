from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User,Group
from courses.models import Course, Trajectory, UserCourseTrajectory, TrajectoryCourse
from myapp.models import UserCourse
from user_management.utils import send_course_assignment_email, send_trajectory_assignment_email
import logging

logger = logging.getLogger(__name__)




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
