from . import views
from django.urls import path

app_name = 'tech_support'

urlpatterns = [
    path('chat/', views.SupportChatView.as_view(), name='support_chat'),
]