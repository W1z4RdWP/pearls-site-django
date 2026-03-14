"""
ASGI config для отдельного сервиса messenger.
Запускается на отдельном порту и обрабатывает только WebSocket соединения.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APPS_DIR = BASE_DIR / 'apps'
sys.path.insert(0, str(APPS_DIR))

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import messenger.routing

# WebSocket для messenger + минимальный HTTP (для health checks)
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Может понадобиться для проверок здоровья
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                messenger.routing.websocket_urlpatterns
            )
        )
    ),
})