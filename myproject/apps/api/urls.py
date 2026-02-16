from django.urls import path
from . import views
from . import views_frontend
from shop import views as shop_views

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
    path('frontend/login/', views_frontend.login_view, name='frontend_login'),
    path('frontend/logout/', views_frontend.logout_view, name='frontend_logout'),

    # Shop API — данные для фронтенда (магазин работает на React)
    path('shop/products/', shop_views.api_products_list, name='api_shop_products'),
    path('shop/product/details/', shop_views.product_details, name='api_shop_product_details'),
    path('shop/order/', shop_views.order_product, name='api_shop_order'),
    path('shop/orders/count/', shop_views.orders_count, name='api_shop_orders_count'),
    path('shop/orders/history/', shop_views.api_order_history, name='api_shop_order_history'),
    path('shop/admin/users/', shop_views.api_users_with_orders, name='api_shop_users_with_orders'),
    path('shop/admin/user/<int:user_id>/orders/', shop_views.api_user_orders_admin, name='api_shop_user_orders_admin'),
    path('shop/product/create/', shop_views.api_create_product, name='api_shop_create_product'),

    # Дашборд builder (панель управления)
    path('builder/dashboard/', views_frontend.dashboard_data, name='api_builder_dashboard'),
    path('changelog/', views_frontend.changelog_data, name='api_changelog'),

    # Профиль пользователя для React
    path('users/user_info/', views_frontend.user_info, name='api_user_info'),
    path('users/profile/', views_frontend.profile_page, name='api_profile_page'),
    path('users/profile/update/', views_frontend.update_profile, name='api_profile_update'),
]