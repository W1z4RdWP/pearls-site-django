from django.contrib.auth.models import User
from .models import Course, Trajectory, Certificate
import logging

logger = logging.getLogger(__name__)




def issue_certificate(user: User, course: Course = None, trajectory: Trajectory = None) -> Certificate:
    """
    Выдает сертификат пользователю за завершение курса или траектории.
    
    Args:
        user: Пользователь, которому выдается сертификат
        course: Курс (если сертификат за курс)
        trajectory: Траектория (если сертификат за траекторию)
        
    Returns:
        Certificate: Выданный сертификат или None, если сертификат не нужен
        
    Raises:
        ValueError: Если не указан ни курс, ни траектория, или указаны оба
    """

    if not course and not trajectory:
        raise ValueError("Необходимо указать либо курс, либо траекторию")
    
    if course and trajectory:
        raise ValueError("Нельзя указывать одновременно курс и траекторию")
    
    # Проверяем, нужно ли выдавать сертификат
    if course:
        if not course.certificate:
            logger.info(f"Сертификат не выдается для курса {course.title} (настройка отключена)")
            return None
            
        # Проверяем, не выдан ли уже сертификат
        existing_cert = Certificate.objects.filter(user=user, course=course).first()
        if existing_cert:
            logger.info(f"Сертификат для курса {course.title} уже выдан пользователю {user.username}")
            return existing_cert
            
        # Создаем сертификат за курс
        certificate = Certificate.objects.create(
            user=user,
            course=course,
            certificate_type='course'
        )
        logger.info(f"Выдан сертификат {certificate.certificate_id} пользователю {user.username} за курс {course.title}")
        
    else:  # trajectory
        if not trajectory.certificate:
            logger.info(f"Сертификат не выдается для траектории {trajectory.name} (настройка отключена)")
            return None
            
        # Проверяем, не выдан ли уже сертификат
        existing_cert = Certificate.objects.filter(user=user, trajectory=trajectory).first()
        if existing_cert:
            logger.info(f"Сертификат для траектории {trajectory.name} уже выдан пользователю {user.username}")
            return existing_cert
            
        # Создаем сертификат за траекторию
        certificate = Certificate.objects.create(
            user=user,
            trajectory=trajectory,
            certificate_type='trajectory'
        )
        logger.info(f"Выдан сертификат {certificate.certificate_id} пользователю {user.username} за траекторию {trajectory.name}")
    
    return certificate




def get_user_certificates(user: User) -> dict:
    """
    Получает все сертификаты пользователя, разделенные по типам.
    
    Args:
        user: Пользователь
        
    Returns:
        dict: Словарь с ключами 'course_certificates' и 'trajectory_certificates'
    """
    
    course_certificates = Certificate.objects.filter(
        user=user,
        certificate_type='course'
    ).select_related('course').order_by('-issued_at')
    
    trajectory_certificates = Certificate.objects.filter(
        user=user,
        certificate_type='trajectory'
    ).select_related('trajectory').order_by('-issued_at')
    
    return {
        'course_certificates': course_certificates,
        'trajectory_certificates': trajectory_certificates,
        'total_count': course_certificates.count() + trajectory_certificates.count()
    }
