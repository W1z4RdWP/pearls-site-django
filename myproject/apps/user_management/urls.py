from django.urls import path

from . import views

app_name = 'user_management'

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/step1/', views.UserCreateStep1View.as_view(), name='user_create_step1'),
    path('users/add/step2/', views.UserCreateStep2View.as_view(), name='user_create_step2'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/detailed/', views.UserEditDetailedView.as_view(), name='user_edit_detailed'),
    path('user/<int:pk>/password/', views.UserPasswordChangeView.as_view(), name='user_password_change'),
    path('users/<int:pk>/progress/', views.UserProgressDashboardView.as_view(), name='user_progress'),
    path('users/<int:pk>/progress/export_excel/', views.export_user_progress_excel, name='user_progress_export_excel'),
    path('users/<int:pk>/quiz-attempts/', views.UserQuizAttemptsView.as_view(), name='user_quiz_attempts'),
    path('users/<int:user_id>/quiz/<int:quiz_id>/unlock/', views.unlock_quiz_access, name='unlock_quiz_access'),
    path('users/quiz_report/<int:quiz_id>/', views.UserQuizReportView.as_view(), name='user_quiz_report'),
    path('roles/manage/', views.role_manage, name='role_manage'),
    path('roles/delete/<int:role_id>/', views.role_delete, name='role_delete'),
    path('roles/<int:role_id>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:role_id>/responsible/', views.role_responsible_manage, name='role_responsible_manage'),
    path('roles/<int:role_id>/users/', views.role_users_json, name='role_users_json'),
    path('roles/all/', views.roles_all_json, name='roles_all_json'),
    path('lessons/<int:lesson_id>/allowed-roles/', views.lesson_allowed_roles_json, name='lesson_allowed_roles_json'),
    path('lessons/<int:lesson_id>/allowed-roles/add/', views.lesson_add_allowed_role, name='lesson_add_allowed_role'),
    path('lessons/<int:lesson_id>/allowed-roles/<int:role_id>/remove/', views.lesson_remove_allowed_role, name='lesson_remove_allowed_role'),


    # Административная панель статистики DASCOIN
    path('admin/dascoin_dashboard/', views.AdminDashboardView.as_view(), name='admin_dascoin_dashboard'),
    path('admin/stats/export/excel/', views.export_admin_stats_excel, name='export_admin_stats_excel'),
    path('admin/stats/export/pdf/', views.export_admin_stats_pdf, name='export_admin_stats_pdf'),

    # Административный просмотр транзакций пользователей
    path('admin/user/<int:user_id>/transactions/', views.AdminUserTransactionsView.as_view(), name='admin_user_transactions'),
    path('admin/user/<int:user_id>/transactions/export/excel/', views.export_admin_user_transactions_excel, name='export_admin_user_transactions_excel'),
    path('admin/user/<int:user_id>/transactions/export/pdf/', views.export_admin_user_transactions_pdf, name='export_admin_user_transactions_pdf'),

    # API endpoints для назначения курсов
    path('api/groups/with-courses/', views.api_get_groups_with_courses, name='api_get_groups_with_courses'),
    path('api/groups/<int:group_id>/courses/', views.api_get_group_courses, name='api_get_group_courses'),
    path('api/courses/search/', views.api_search_courses, name='api_search_courses'),
    path('api/users/<int:user_id>/assign-courses/', views.api_assign_courses_to_user, name='api_assign_courses_to_user'),

    # API endpoints для назначения траекторий
    path('api/groups/with-trajectories/', views.api_get_groups_with_trajectories, name='api_get_groups_with_trajectories'),
    path('api/groups/<int:group_id>/trajectories/', views.api_get_group_trajectories, name='api_get_group_trajectories'),
    path('api/trajectories/search/', views.api_search_trajectories, name='api_search_trajectories'),
    path('api/users/<int:user_id>/assign-trajectories/', views.api_assign_trajectories_to_user, name='api_assign_trajectories_to_user'),

    # Отмена назначения обучения
    path('users/<int:user_id>/unassign-course/<int:user_course_id>/', views.unassign_course_from_user, name='unassign_course'),
    path('users/<int:user_id>/unassign-trajectory/<int:user_trajectory_id>/', views.unassign_trajectory_from_user, name='unassign_trajectory'),
    
    # Блокировка/разблокировка курса
    path('users/<int:user_id>/toggle-course-block/<int:user_course_id>/', views.toggle_course_block, name='toggle_course_block'),

]