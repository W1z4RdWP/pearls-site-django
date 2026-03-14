"""
Экстренные настройки CSRF для решения критических проблем.
Используйте только в крайних случаях!
"""

from .prod import *

# ВНИМАНИЕ: Эти настройки снижают безопасность!
# Используйте только для диагностики и временного решения проблем.

# Отключаем CSRF защиту (ОПАСНО!)
# CSRF_COOKIE_SECURE = False
# CSRF_COOKIE_HTTPONLY = False
# CSRF_COOKIE_SAMESITE = None

# Альтернативные настройки для решения проблем с CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://lc.smileterritory.ru',
    'https://www.lc.smileterritory.ru',
    'http://lc.smileterritory.ru',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://localhost:8000',
    'https://127.0.0.1:8000',
]

# Более мягкие настройки CSRF
CSRF_COOKIE_SECURE = False  # Временно отключаем для HTTP
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# Настройки сессий
SESSION_COOKIE_SECURE = False  # Временно отключаем для HTTP
SESSION_COOKIE_SAMESITE = 'Lax'

# Отключаем HSTS для тестирования
SECURE_HSTS_SECONDS = 0

print("⚠️  ВНИМАНИЕ: Используются экстренные настройки CSRF!")
print("⚠️  Безопасность снижена! Используйте только для диагностики!")
