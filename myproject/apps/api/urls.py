from django.urls import path
from .views import views
from . import views_frontend
from .views.views_frontend import views_shop as shop_views
from .views.views_frontend import views_users as users_views
from .views.views_frontend import views_messenger as messenger_views
from .views.views_frontend import views_myapp as myapp_views
from .views.views_frontend import views_user_management as user_management_views
from .views.views_frontend import views_courses as courses_views
from .views.views_frontend import views_builder as builder_views
from .views.views_frontend import views_tech_support as tech_support_views
from .views.views_frontend import views_reports as reports_views
from builder.views.api_views import api_search_users
from quizzes.views import search_quizzes_ajax

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
    path('builder/content/', builder_views.api_master_detail_content, name='api_builder_content'),
    path('builder/lesson/<int:pk>/', builder_views.api_lesson_detail, name='api_builder_lesson_detail'),
    path('builder/trajectory-management/', builder_views.api_trajectory_management, name='api_builder_trajectory_management'),
    path('builder/courses/', builder_views.api_course_list, name='api_builder_course_list'),
    path('builder/course/<slug:slug>/delete/', builder_views.api_course_delete, name='api_builder_course_delete'),
    path('builder/incident-courses/', builder_views.api_incident_course_list, name='api_builder_incident_course_list'),
    path('builder/incident-courses/course/<slug:slug>/delete/', builder_views.api_incident_course_delete, name='api_builder_incident_course_delete'),
    path('builder/add/', builder_views.api_lesson_form_create, name='api_builder_lesson_add'),
    path('builder/add/<int:category_id>/', builder_views.api_lesson_form_create, name='api_builder_lesson_add_with_category'),
    path('builder/lesson/<int:pk>/edit/', builder_views.api_lesson_form_edit, name='api_builder_lesson_edit'),
    path('builder/lesson/delete/info/', builder_views.api_lesson_delete_info, name='api_builder_lesson_delete_info'),
    path('builder/lesson/delete/', builder_views.api_lesson_delete, name='api_builder_lesson_delete'),
    path('builder/categories/root/', builder_views.api_add_root_category, name='api_builder_category_add_root'),
    path('builder/categories/sub/', builder_views.api_add_subcategory, name='api_builder_category_add_sub'),
    path('builder/categories/rename/', builder_views.api_rename_category, name='api_builder_category_rename'),
    path('builder/categories/delete/stats/', builder_views.api_category_delete_stats, name='api_builder_category_delete_stats'),
    path('builder/categories/delete/', builder_views.api_delete_category, name='api_builder_category_delete'),
    path('builder/incidents/', builder_views.api_incidents_list, name='api_builder_incidents'),
    path('builder/incidents/<int:pk>/decline/', builder_views.api_incident_decline, name='api_builder_incident_decline'),
    path('changelog/', views_frontend.changelog_data, name='api_changelog'),

    # MyApp API — история изменений для React
    path('myapp/changelog/', myapp_views.api_changelog_list, name='api_myapp_changelog'),

    # Профиль пользователя для React
    path('users/user_info/', views_frontend.user_info, name='api_user_info'),
    path('users/profile/', views_frontend.profile_page, name='api_profile_page'),
    path('users/profile/update/', views_frontend.update_profile, name='api_profile_update'),
    path('users/profile/all-badges/', views_frontend.all_badges_api, name='api_all_badges'),
    path('users/profile/all-achievements/', views_frontend.all_achievements_api, name='api_all_achievements'),

    # Courses API — траектории/курсы и сертификаты для React
    path('courses/trajectories/', courses_views.api_trajectory_list, name='api_courses_trajectories'),
    path('courses/user-certificates/', courses_views.api_user_certificates, name='api_courses_user_certificates'),
    path('courses/create-course/', courses_views.api_create_course, name='api_courses_create_course'),
    path('courses/course/<slug:slug>/', courses_views.api_course_detail, name='api_courses_course_detail'),
    path('courses/course/<slug:slug>/start/', courses_views.api_start_course, name='api_courses_start_course'),
    path('courses/course/<slug:slug>/reorder-materials/', courses_views.api_reorder_materials, name='api_courses_reorder_materials'),
    path('courses/lesson/<int:lesson_id>/edit/', courses_views.api_edit_lesson, name='api_courses_edit_lesson'),
    path('courses/course/<slug:slug>/edit/', courses_views.api_course_edit, name='api_courses_course_edit'),
    path('courses/course/<slug:slug>/create-lesson/', courses_views.api_create_lesson, name='api_courses_create_lesson'),
    path('courses/course/<slug:slug>/add-lesson/', courses_views.api_add_lesson, name='api_courses_add_lesson'),

    # Builder/Quizzes — поиск для форм (create course и др.)
    path('builder/users/search/', api_search_users, name='api_builder_search_users'),
    path('quizzes/search/', search_quizzes_ajax, name='api_quizzes_search'),

    # Users API — транзакции DASCOIN для React
    path('users/transactions/', users_views.api_transactions, name='api_users_transactions'),
    path('users/quiz-attempts-report/', users_views.api_quiz_attempts_report, name='api_users_quiz_attempts_report'),

    # User Management API — управление пользователями для React
    path('user_management/users/', user_management_views.api_user_list, name='api_user_management_user_list'),
    path('user_management/users/add/step1/', user_management_views.api_user_create_step1, name='api_user_management_user_create_step1'),
    path('user_management/users/add/step2/data/', user_management_views.api_user_create_step2_data, name='api_user_management_user_create_step2_data'),
    path('user_management/users/add/step2/', user_management_views.api_user_create_step2, name='api_user_management_user_create_step2'),
    path('user_management/users/<int:pk>/edit/data/', user_management_views.api_user_edit_data, name='api_user_management_user_edit_data'),
    path('user_management/users/<int:pk>/edit/', user_management_views.api_user_update, name='api_user_management_user_update'),
    path('user_management/roles/create/', user_management_views.api_role_create, name='api_user_management_role_create'),
    path('user_management/roles/<int:role_id>/update/', user_management_views.api_role_update, name='api_user_management_role_update'),
    path('user_management/roles/<int:role_id>/delete/', user_management_views.api_role_delete, name='api_user_management_role_delete'),
    path('user_management/roles/<int:role_id>/set-responsible/', user_management_views.api_role_set_responsible, name='api_user_management_role_set_responsible'),
    path('user_management/roles/<int:role_id>/users/', user_management_views.api_role_users, name='api_user_management_role_users'),
    path('user_management/users/<int:pk>/password/', user_management_views.api_user_password_change, name='api_user_management_user_password_change'),

    # User Management API — административная панель DASCOIN
    path('user_management/admin/dascoin_dashboard/', user_management_views.api_admin_dascoin_dashboard, name='api_user_management_admin_dascoin_dashboard'),
    path('user_management/admin/user/<int:user_id>/transactions/', user_management_views.api_admin_user_transactions, name='api_user_management_admin_user_transactions'),

    # Users API — смена пароля
    path('users/password_change/', users_views.api_password_change, name='api_users_password_change'),

    # Messenger API
    path('messenger/chat_rooms/', messenger_views.api_chat_rooms, name='api_messenger_chat_rooms'),
    path('messenger/chat_room/create/', messenger_views.api_chat_room_create, name='api_messenger_chat_room_create'),
    path('messenger/chat_room/<str:room_id>/', messenger_views.api_chat_room_data, name='api_messenger_chat_room_data'),
    path('messenger/chat_room/<str:room_id>/send/', messenger_views.api_chat_room_send_message, name='api_messenger_chat_room_send_message'),

    # Reports API — проверка заданий для React
    path('reports/homework-check-dashboard/', reports_views.api_homework_check_dashboard, name='api_reports_homework_check_dashboard'),

    # Tech Support API — обращение в поддержку (React)
    path('tech_support/chat/', tech_support_views.api_ticket_create, name='api_tech_support_ticket_create'),
    path('tech_support/my/tickets/', tech_support_views.api_my_ticket_list, name='api_tech_support_my_ticket_list'),
    path('tech_support/tickets/', tech_support_views.api_ticket_list_staff, name='api_tech_support_ticket_list_staff'),
    path('tech_support/dashboard/', tech_support_views.api_staff_dashboard, name='api_tech_support_staff_dashboard'),
    path('tech_support/reports/', tech_support_views.api_ticket_reports, name='api_tech_support_ticket_reports'),
]