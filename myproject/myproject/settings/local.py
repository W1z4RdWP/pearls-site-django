## myproject/settings/local.py

from .base import *
from .local_envs import DJANGO_SECRET_KEY

SECRET_KEY = os.getenv(DJANGO_SECRET_KEY, "default")

DEBUG = True

ALLOWED_HOSTS = ["*"]

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": "sqlite3.sql",
#     }
# }


DATABASES = {
    'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('LOCAL_DJANGO_DB_NAME'), # LOCAL_DJANGO_DB_NAME /
            'USER': os.getenv('LOCAL_DJANGO_DB_USER'), # DJANGO_DB_USER /
            'PASSWORD': os.getenv('LOCAL_DJANGO_DB_PASSWD'), # DJANGO_DB_PASSWD /
            'HOST': os.getenv('LOCAL_DJANGO_DB_HOST'), # DJANGO_DB_HOST / 
            'PORT': os.getenv('LOCAL_DJANGO_DB_PORT'), # DJANGO_DB_PORT /
            'CONN_MAX_AGE': 60 * 10, # Не разрывать соединения пользователей с БД в течение 10 минут
            'OPTIONS' :{
                'client_encoding': 'UTF8',
            }
    }
}

