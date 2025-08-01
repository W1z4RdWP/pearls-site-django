from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('<int:notification_id>/mark-read/', views.mark_as_read, name='mark_as_read'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('count/', views.notification_count, name='notification_count'),
    path('dropdown/', views.notification_dropdown, name='notification_dropdown'),
    path('clear-old/', views.clear_old_notifications, name='clear_old_notifications'),
] 