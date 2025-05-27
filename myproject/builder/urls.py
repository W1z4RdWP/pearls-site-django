from django.urls import path

from . import views

app_name = 'builder'

urlpatterns = [
    path('', views.LessonMasterDetailView.as_view(), name='lesson_master'),
    path('lesson/<int:pk>/', views.LessonMasterDetailView.as_view(), name='lesson_detail'),
    path('lesson/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),
    path('add/', views.LessonCreateView.as_view(), name='lesson_add'),
]