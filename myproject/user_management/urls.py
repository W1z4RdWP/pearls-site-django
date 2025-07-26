from django.urls import path

from . import views

app_name = 'user_management'

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/step1/', views.UserCreateStep1View.as_view(), name='user_create_step1'),
    path('users/add/step2/', views.UserCreateStep2View.as_view(), name='user_create_step2'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('user/<int:pk>/password/', views.UserPasswordChangeView.as_view(), name='user_password_change'),
    path('users/<int:pk>/progress/', views.UserProgressDashboardView.as_view(), name='user_progress'),
    path('users/quiz_report/<int:quiz_id>/', views.UserQuizReportView.as_view(), name='user_quiz_report'),
    path('roles/manage/', views.role_manage, name='role_manage'),
    path('roles/delete/<int:role_id>/', views.role_delete, name='role_delete'),
    path('roles/<int:role_id>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:role_id>/responsible/', views.role_responsible_manage, name='role_responsible_manage'),
    path('roles/<int:role_id>/users/', views.role_users_json, name='role_users_json'),
]