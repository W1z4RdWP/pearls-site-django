from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class MentorRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки, что пользователь является наставником"""

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False

        if user.is_superuser or user.is_staff:
            return True

        # Проверяем роль наставника в профиле
        try:
            return user.profile.is_mentor_user()
        except:
            return False




def is_mentor(user):
    """
    Проверяет, является ли пользователь наставником.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    try:
        return user.profile.is_mentor_user()
    except:
        return False