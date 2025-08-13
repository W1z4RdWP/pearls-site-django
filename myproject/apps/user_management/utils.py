from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

def send_user_credentials_email(user, password):
    """
    Отправляет email с данными для входа пользователю
    """
    subject = 'Данные для входа в систему'
    
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