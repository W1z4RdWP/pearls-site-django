from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('telegram/register/', views.telegram_register, name='telegram_register'),
]