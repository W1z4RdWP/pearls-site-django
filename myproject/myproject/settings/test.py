from .base import *
import os

SECRET_KEY = os.getenv("SECRET_DJANGO", 'default')

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # in-memory БД для тестов
    }
}