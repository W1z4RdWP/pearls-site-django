"""
ASGI config for myproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import sys
from pathlib import Path

# Добавляем папку apps в PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR / 'apps'
sys.path.insert(0, str(APPS_DIR))

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_asgi_application()
