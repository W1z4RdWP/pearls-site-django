"""
ASGI config for myproject project.
Основной сервис - только HTTP (messenger вынесен отдельно).
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR / 'apps'
sys.path.insert(0, str(APPS_DIR))

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Только HTTP - WebSocket убран, так как messenger отделен
application = get_asgi_application()