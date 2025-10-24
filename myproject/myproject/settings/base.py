## myproject/settings/base.py

from pathlib import Path
import os
import sys

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Добавляем папку apps в PYTHONPATH
APPS_DIR = BASE_DIR / 'apps'
sys.path.insert(0, str(APPS_DIR))

#SECRET_KEY = os.getenv('SECRET_DJANGO') # DJANGO_SECRET_KEY / SECRET_DJANGO


# JWT настройки для Telegram авторизации
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_MINUTES = 1440 # Токен действителен 10 минут
 
#DEBUG = True

# allowed_hosts = os.getenv('DJANGO_ALLOWED_HOSTS', '')
# ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(',')] if allowed_hosts else []

ALLOWED_HOSTS = ["*"]

INTERNAL_IPS = [
    "0.0.0.0",
    "127.0.0.1",
    "10.0.1.100",
    "10.1.1.30",
    "10.0.0.40",
    "192.168.0.100",
    "172.18.0.4"
]



# Application definition

INSTALLED_APPS = [

    "admin_interface",
    "colorfield",
    'dal',
    'dal_select2',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    #'django.contrib.sessions',
    'django.contrib.messages',
    "whitenoise.runserver_nostatic",
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    'captcha',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_ckeditor_5',
    'nested_admin',
    'debug_toolbar',
    'qsessions',
    'rangefilter',
    'rest_framework',
    'widget_tweaks',    

    'myapp.apps.MyappConfig',
    'api.apps.ApiConfig',
    'users.apps.UsersConfig',
    'courses.apps.CoursesConfig',
    'quizzes.apps.QuizzesConfig',
    'builder.apps.BuilderConfig', # БЗ. Конструктор траекторий из уроков.
    'user_management.apps.UserManagementConfig',
    'gamification.apps.GamificationConfig',
    'notifications.apps.NotificationsConfig',
    'tech_support.apps.TechSupportConfig',
]

X_FRAME_OPTIONS = "SAMEORIGIN"              # allows you to use modals insated of popups
SILENCED_SYSTEM_CHECKS = ["security.W019"]  # ignores redundant warning messages

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware', # django-debug toolbar = панель отладки djt
    #'django.middleware.cache.UpdateCacheMiddleware', # кэш
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'qsessions.middleware.SessionMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'myapp.middleware.CSRFDebugMiddleware',  # Отладка CSRF проблем
    'quizzes.middleware.prevent_refresh.PreventRefreshMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'courses.middleware.ExternalUserActivityMiddleware',  # Логирование активности внешних пользователей
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
   # 'django.middleware.cache.FetchFromCacheMiddleware', # кэш
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'myapp.context_processors.get_changelog', # Кастомный контекстный процессор
                'myapp.context_processors.nav_menu',
            ],
        },
    },
]

MEDIA_URL = '/media/'  # URL для доступа к медиафайлам
MEDIA_ROOT = BASE_DIR / 'media'  # Папка для хранения медиафайлов

STORAGES = {
    "default": { 
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

WSGI_APPLICATION = 'myproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': os.getenv('DJANGO_DB_NAME'),
#             'USER': os.getenv('DJANGO_DB_USER'),
#             'PASSWORD': os.getenv('DJANGO_DB_PASSWD'),
#             'HOST': os.getenv('DJANGO_DB_HOST'),
#             'PORT': os.getenv('DJANGO_DB_PORT'),
#             'OPTIONS' :{
#                 'client_encoding': 'UTF8',
#             }
#     }
# }

# DATABASES = {
#     'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': os.getenv('DJANGO_DB_NAME'), # DJANGO_DB_NAME /
#             'USER': os.getenv('DJANGO_DB_USER'), # DJANGO_DB_USER /
#             'PASSWORD': os.getenv('DJANGO_DB_PASSWD'), # DJANGO_DB_PASSWD /
#             'HOST': os.getenv('DJANGO_DB_HOST'), # DJANGO_DB_HOST / 
#             'PORT': os.getenv('DJANGO_DB_PORT'), # DJANGO_DB_PORT /
#             'CONN_MAX_AGE': 60 * 10, # Не разрывать соединения пользователей с БД в течение 10 минут
#             'OPTIONS' :{
#                 'client_encoding': 'UTF8',
#             }
#     }
# }

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": "sqlite3.sql",
#     }
# }


## файловое кэширование
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
#         'LOCATION': os.path.join(BASE_DIR, 'myproject_cache')
#     }
# }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
    'users.backends.ApprovalBackend',
    'django.contrib.auth.backends.ModelBackend',
]



# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Saratov'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


# Указывает URL для статических файлов
STATIC_URL = '/static/'

# Директория, куда collectstatic соберет файлы для продакшена
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Дополнительные директории со статикой (общие файлы проекта)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Папка с глобальными файлами
]


SITE_URL = os.getenv('SITE_URL')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST') # SMTP сервер
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587)) if os.getenv('EMAIL_PORT') else 587
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', '').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', '').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

customColorPalette = [
    {"color": "hsl(4, 90%, 58%)", "label": "Red"},
    {"color": "hsl(340, 82%, 52%)", "label": "Pink"},
    {"color": "hsl(291, 64%, 42%)", "label": "Purple"},
    {"color": "hsl(262, 52%, 47%)", "label": "Deep Purple"},
    {"color": "hsl(231, 48%, 48%)", "label": "Indigo"},
    {"color": "hsl(207, 90%, 54%)", "label": "Blue"},
]
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = 'bootstrap5'

SESSION_ENGINE = 'qsessions.backends.db'
SESSION_COOKIE_AGE = 7200 * 12 # Время сессии в секундах (2 часа)

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'users:login'
LOGIN_URL = 'users:login'

# Кастомная страница ошибки CSRF
CSRF_FAILURE_VIEW = 'myapp.views.csrf_failure_view'

# Дополнительные настройки CSRF для стабильной работы
CSRF_COOKIE_AGE = 31449600  # 1 год
CSRF_COOKIE_DOMAIN = None  # Автоматическое определение домена
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_PATH = '/'

CKEDITOR_5_ALLOW_ALL_FILE_TYPES = True
CKEDITOR_5_UPLOAD_FILE_TYPES = ['jpeg', 'pdf', 'png', 'jpg', 'mp4']

CKEDITOR_5_FILE_STORAGE = "courses.storage.CustomStorage"

CKEDITOR_5_UPLOAD_FILE_VIEW_NAME = "ckeditor5_custom_upload_file" # ?
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff" # ?


CKEDITOR_5_CONFIGS = {
    "extends": {

        "language": "ru",
        'toolbar': {
            'items': [
                '|', 'heading',
                '|', 'outdent', 'indent',
                '|', 'bold', 'italic', 'underline', 'strikethrough', 'code', 'subscript', 'superscript',
                'highlight',
                '|', 'codeBlock', 'insertImage', 'bulletedList', 'numberedList', 'todoList',
                '|', 'blockQuote',
                '|', 'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'removeFormat',
                'insertTable', 
                '|', 'htmlEmbed', 'link', 
            ],
            'shouldNotGroupWhenFull': True
        },
        "image": {
            "toolbar": [
                '|', "imageTextAlternative",
                "|", "imageStyle:alignLeft", "imageStyle:alignRight", "imageStyle:alignCenter", "imageStyle:side",
                "|", "toggleImageCaption",
                "|"
            ],
            "styles": [
                "full",
                "side",
                "alignLeft",
                "alignRight",
                "alignCenter",
            ],
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
                "toggleTableCaption"
            ],
            "tableProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
                "defaultProperties": {
                    "width": "100%",
                    "borderWidth": "1px"
                }
            },
            "tableCellProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
                "defaultProperties": {
                    "width": "auto",
                    "height": "auto"
                }
            }
        },
        "list": {
            "properties": {
                "styles": True,
                "startIndex": True,
                "reversed": True,
            }
        },
        'fontSize': {
            'options': [
                9, 10, 11, 12, 13, 14, 15, 16, 
                'default', 18, 20, 22, 24, 28, 32, 36
            ],
            'supportAllValues': True
        },
        "htmlSupport": {
            "allow": [
                {
                    "name": "img",
                    "attributes": {
                        "class": True,
                        "style": True
                    },
                    "name": "span",
                    "attributes": {
                        "style": True
                    }
                },
                {
                    "name": "table",
                    "attributes": ["style", "width", "height", "border"]
                },
                {
                    "name": "td",
                    "attributes": ["style", "width", "height", "colspan", "rowspan"]
                },
                {
                    "name": "th",
                    "attributes": ["style", "width", "height", "colspan", "rowspan"]
                }
            ]
        }
    },
    "noTablesImages": {
        "language": "ru",
        "toolbar": {
            "items": [
                '|', 'heading',
                '|', 'outdent', 'indent',
                '|', 'bold', 'italic', 'link', 'underline', 'strikethrough', 'code', 'subscript', 'superscript',
                'highlight',
                '|', 'codeBlock', 'bulletedList', 'numberedList', 'todoList',
                '|', 'blockQuote',
                '|', 'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'removeFormat',
                '|',
            ],
            "shouldNotGroupWhenFull": True
        },
        
    },
}

## main logging conf
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'audit_format': {
            'format': '{asctime} - USER: {user} - ACTION: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        # Общий файл ошибок
        'error_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/errors.log',
            'formatter': 'verbose'
        },
        # Файл аудита действий пользователей
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/audit.log',
            'maxBytes': 1024*1024*10,
            'backupCount': 5,
            'formatter': 'audit_format'
        },
    },
    'loggers': {
        # Перехват всех ошибок проекта
        'django': {
            'handlers': ['error_file'],
            'level': 'WARNING',
            'propagate': True,
        },
        # Кастомный логгер для аудита
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY')
# RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY')

