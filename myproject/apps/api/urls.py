from django.urls import path
from . import views
from . import views_frontend

app_name = 'api'

urlpatterns = [
    path('user/register/', views.user_register, name='api_user_register'),

    # Telegram endpoints
    path('telegram/register/', views.telegram_register, name='telegram_register'),
    path('telegram/auth/', views.telegram_auth, name='telegram_auth'),
    path('telegram/auth-existing', views.telegram_auth_existing, name='telegram_auth_existing'),
    path('telegram/token/', views.generate_auth_token, name='generate_auth_token'),
    path('telegram/metrics-check/', views.telegram_metrics_check, name='telegram_metrics_check'),
    path('short-token/', views.generate_short_token, name='generate_short_token'),
    path('s/<str:short_token>/', views.short_token_auth, name='short_token_auth'),

    # Frontend endpoints
    path('frontend/layout/', views_frontend.layout_data, name='frontend_layout'),
    path('frontend/courses/', views_frontend.home_courses, name='frontend_courses'),
]