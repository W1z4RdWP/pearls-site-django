## myproject/settings/prod.py

from .base import *

DEBUG = False

SECRET_KEY = os.getenv("SECRET_DJANGO")

allowed_hosts = os.getenv('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(',')] if allowed_hosts else []

DATABASES = {
    'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DJANGO_DB_NAME'), # DJANGO_DB_NAME /
            'USER': os.getenv('DJANGO_DB_USER'), # DJANGO_DB_USER /
            'PASSWORD': os.getenv('DJANGO_DB_PASSWD'), # DJANGO_DB_PASSWD /
            'HOST': os.getenv('DJANGO_DB_HOST'), # DJANGO_DB_HOST / 
            'PORT': os.getenv('DJANGO_DB_PORT'), # DJANGO_DB_PORT /
            'CONN_MAX_AGE': 60 * 10, # Не разрывать соединения пользователей с БД в течение 10 минут
            'OPTIONS' :{
                'client_encoding': 'UTF8',
            }
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}



CACHE_MIDDLEWARE_ALIAS  = 'default' # cache alias
CACHE_MIDDLEWARE_SECONDS = 600 # number of seconds each page should be cached.
CACHE_MIDDLEWARE_KEY_PREFIX = 'myproject'  # name of site if multiple sites are used


# CSRF_TRUSTED_ORIGINS = ['https://epicsite.smileterritory.ru']

# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
