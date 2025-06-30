from django.urls import path

from . import views
from .views import DashboardView

app_name = 'builder'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('content/', views.LessonMasterDetailView.as_view(), name='lesson_master'),
    path('lesson/<int:pk>/', views.LessonMasterDetailView.as_view(), name='lesson_detail'),
    path('lesson/<int:pk>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),
    path('lesson/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),
    path('add/', views.LessonCreateView.as_view(), name='lesson_add'),
    path('add/<int:category_id>/', views.LessonCreateView.as_view(), name='lesson_add_with_category'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]