from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    app_label = 'courses'

    def ready(self):
        import courses.signals  # активация сигналов
