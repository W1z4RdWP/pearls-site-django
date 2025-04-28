from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class ApprovalBackend(ModelBackend):
    def user_can_authenticate(self, user):
        is_active = super().user_can_authenticate(user)
        return is_active and hasattr(user, 'profile') and user.profile.is_approved