from math import remainder
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse




def get_user_privilege_level(user):
    if user.is_superuser:
        return 4
    if user.is_staff:
        return 3
    if user.profile.is_mentor_user:
        return 2
    return 1




def send_user_credentials_email(user, password):
    """
    Отправляет email с данными для входа пользователю
    """
    subject = 'Данные для входа в систему'
    
    # Генерируем ссылку для входа
    login_url = f"{settings.SITE_URL}{reverse('users:login')}"

    # Генерируем ссылку для смены пароля
    change_password_url = f"{settings.SITE_URL}{reverse('users:password_change')}"    
    # Получаем ФИО пользователя
    full_name = user.get_full_name()
    if not full_name:
        full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.username
    
    # Рендерим HTML шаблон
    html_message = render_to_string(
        'user_management/email/user_credentials.html',
        {
            'user': user,
            'username': user.username,
            'password': password,
            'full_name': full_name,
            'change_password_url': change_password_url,
            'login_url': login_url,
        }
    )
    
    # Отправляем email
    try:
        send_mail(
            subject=subject,
            message='Текстовое сообщение',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False


def send_course_assignment_email(user, course):
    """
    Отправляет email уведомление о назначении курса (или курса-инцидента).
    """
    is_incident = bool(getattr(course, 'is_incident', False))
    if is_incident:
        subject = f'Вам назначен курс-инцидент: {course.title}'
    else:
        subject = f'Вам назначен курс: {course.title}'
    
    # Получаем ФИО пользователя
    full_name = user.get_full_name()
    if not full_name:
        full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.username
    
    # Генерируем ссылку на курс
    course_url = f"{settings.SITE_URL}{reverse('courses:course_detail', kwargs={'slug': course.slug})}"
    
    # Рендерим HTML шаблон
    html_message = render_to_string(
        'user_management/email/course_assignment.html',
        {
            'user': user,
            'course': course,
            'full_name': full_name,
            'course_url': course_url,
            'is_incident': is_incident,
        }
    )
    
    # Отправляем email
    try:
        from django.core.mail import EmailMultiAlternatives
        
        # Создаем сообщение с альтернативным содержимым
        plain_intro = (
            f'Вам назначен курс-инцидент "{course.title}"'
            if is_incident
            else f'Вам назначен курс "{course.title}"'
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=f'{plain_intro}. Ссылка: {course_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        
        # Добавляем HTML версию
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False


def send_trajectory_assignment_email(user, trajectory):
    """
    Отправляет email уведомление о назначении траектории
    """
    subject = f'Вам назначена траектория обучения: {trajectory.name}'
    
    # Получаем ФИО пользователя
    full_name = user.get_full_name()
    if not full_name:
        full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.username
    
    # Генерируем ссылку на траектории пользователя
    trajectory_url = f"{settings.SITE_URL}{reverse('courses:user_course_trajectory_list')}"
    
    # Получаем первый курс траектории для кнопки "Начать обучение"
    first_course = None
    trajectory_courses = trajectory.trajectorycourse_set.order_by('order').first()
    if trajectory_courses:
        first_course = trajectory_courses.course
        first_course_url = f"{settings.SITE_URL}{reverse('courses:course_detail', kwargs={'slug': first_course.slug})}"
    else:
        first_course_url = trajectory_url
    
    # Рендерим HTML шаблон
    html_message = render_to_string(
        'user_management/email/trajectory_assignment.html',
        {
            'user': user,
            'trajectory': trajectory,
            'full_name': full_name,
            'trajectory_url': trajectory_url,
            'first_course': first_course,
            'first_course_url': first_course_url,
        }
    )
    
    # Отправляем email
    try:
        from django.core.mail import EmailMultiAlternatives
        
        # Создаем сообщение с альтернативным содержимым
        msg = EmailMultiAlternatives(
            subject=subject,
            body=f'Вам назначена траектория обучения "{trajectory.name}". Ссылка: {trajectory_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        
        # Добавляем HTML версию
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False


def format_timedelta(td):
    """Форматирует timedelta в читаемый формат"""
    total_seconds = int(td.total_seconds())
    if total_seconds == 0:
        return "0:00:00"
    days = td.days
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days > 0:
        return f"{days}д {hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
