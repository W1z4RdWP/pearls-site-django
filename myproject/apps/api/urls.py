from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('telegram/register/', views.telegram_register, name='telegram_register'),
    path('telegram/auth/', views.telegram_auth, name='telegram_auth'),
    path('telegram/token/', views.generate_auth_token, name='generate_auth_token'),
    path('short-token/', views.generate_short_token, name='generate_short_token'),
    path('s/<str:short_token>/', views.short_token_auth, name='short_token_auth'),


]