from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('homework-check-dashboard/', views.HomeworkCheckDashboardView.as_view(), name='homework_check_dashboard'),
    path('users-with-learning/', views.UsersWithLearningView.as_view(), name='users_with_learning'),
    path('groups-progress/', views.GroupsProgressView.as_view(), name='groups_progress'),
    path('groups/<int:group_id>/students-progress/', views.GroupStudentsProgressView.as_view(), name='group_students_progress'),

]