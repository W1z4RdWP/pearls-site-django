from django.urls import path
from . import views

urlpatterns = [
   # path('', views.send_feedback, name='send_feedback'),
    path('notifications/', views.notifications, name='notifications'),
    # path('messages/', views.messages_inbox, name='messages_inbox'),
    # path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
]
