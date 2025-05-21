## myproject/settings/local.py

from .base import *


#    from .local_envs import DJANGO_SECRET_KEY

SECRET_KEY = os.getenv(DJANGO_SECRET_KEY, "default")

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "sqlite3.sql",
    }
}