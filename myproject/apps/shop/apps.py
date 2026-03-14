from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    app_label = 'shop'
    
    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        import shop.signals  # noqa