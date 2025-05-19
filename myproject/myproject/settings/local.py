## myproject/settings/local.py

from .base import *

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "sqlite3.sql",
    }
}