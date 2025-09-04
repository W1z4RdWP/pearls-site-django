from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('telegram/register/', views.telegram_register, name='telegram_register'),
    path('telegram/auth/', views.telegram_auth, name='telegram_auth'),
    path('telegram/token/', views.generate_auth_token, name='generate_auth_token'),
]