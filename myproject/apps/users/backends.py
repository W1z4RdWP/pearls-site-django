from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class ApprovalBackend(ModelBackend):
    """Бэкэнд аутентификации пользователей. Если у пользователя задан параметр is_active = True,
    то он может авторизоваться.
    """
    def user_can_authenticate(self, user):
        is_active = super().user_can_authenticate(user)
        return is_active and hasattr(user, 'profile') and user.profile.is_approved


class EmailBackend(ModelBackend):
    """Бэкэнд для аутентификации по email вместо username"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        if username is None or password is None:
            return None
        if '@' in username:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
        else:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None