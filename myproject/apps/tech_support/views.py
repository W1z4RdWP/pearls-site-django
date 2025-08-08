from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class SupportChatView(LoginRequiredMixin, TemplateView):
    template_name = 'tech_support/support_chat.html'