from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    app_label = 'notifications'
    verbose_name = 'Уведомления'
    
    def ready(self):
        import notifications.signals
