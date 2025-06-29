from django.urls import path

from . import views

app_name = 'user_management'

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/progress/', views.UserProgressDashboardView.as_view(), name='user_progress'),
    path('users/quiz_report/<int:quiz_id>/', views.UserQuizReportView.as_view(), name='user_quiz_report'),
]