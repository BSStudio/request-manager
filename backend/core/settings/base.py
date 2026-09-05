"""
Django settings for core project.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

from datetime import timedelta
from ipaddress import ip_network
from pathlib import Path
from re import match

from celery.schedules import crontab
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from django.utils.translation import gettext_lazy as _
from redis.asyncio import Redis as RedisClient

# Build paths inside the project like this: BACKEND_DIR / "subdir"
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = (BACKEND_DIR / ".." / "frontend").resolve()
FRONTEND_ADMIN_DIR = (BACKEND_DIR / ".." / "frontend-admin").resolve()

# URL of the site such as: https://website.example.com
BASE_URL_DOMAIN = config("BASE_URL_DOMAIN", default="localhost:8000")
BASE_URL_HTTPS = config("BASE_URL_HTTPS", default=True, cast=bool)
BASE_URL = f'{"https://" if BASE_URL_HTTPS else "http://"}{BASE_URL_DOMAIN}'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("APP_SECRET_KEY", default=get_random_secret_key())

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# Trusted reverse-proxy networks for resolving the client IP from X-Forwarded-For.
TRUSTED_PROXY_CIDRS = [
    ip_network(cidr, strict=False)
    for cidr in config(
        "TRUSTED_PROXY_CIDRS",
        default="127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
        cast=Csv(),
    )
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.postgres",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "django_celery_results",
    "cacheops",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    "health_check",
    "rest_framework_simplejwt.token_blacklist",
    "phonenumber_field",
    "simple_history",
    "common",
    "video_requests",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.middleware.RequestLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            FRONTEND_DIR / "build",
            FRONTEND_ADMIN_DIR / "build",
            BACKEND_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DATABASE_NAME", default="request_manager_db"),
        "USER": config("DATABASE_USER", default="request_manager"),
        "PASSWORD": config("DATABASE_PASSWORD", default="change_me"),
        "HOST": config("DATABASE_HOST", default="postgres"),
        "PORT": config("DATABASE_PORT", default=5432, cast=int),
    }
}

# Cacheops
# https://github.com/Suor/django-cacheops

CACHEOPS_REDIS = config("CACHE_REDIS", default="redis://redis:6379/0")
CACHEOPS_DEGRADE_ON_FAILURE = True
CACHEOPS = {
    # Automatically cache all gets and queryset fetches
    # to django.contrib.auth models for an hour
    "auth.*": {"ops": {"fetch", "get"}, "timeout": 60 * 60},
    # Cache all queries to Permission
    # 'all' is an alias for {'get', 'fetch', 'count', 'aggregate', 'exists'}
    "auth.permission": {"ops": "all", "timeout": 60 * 60},
    # The user model lives in the common app but needs the same caching as
    # the rest of the auth models
    "common.user": {"ops": {"fetch", "get"}, "timeout": 60 * 60},
    # Enable manual caching on all other models with default timeout of an hour
    # Invalidation is still automatic
    "*.*": {"timeout": 60 * 60},
}

# Celery
# https://docs.celeryproject.org/en/stable/userguide/configuration.html

CELERY_BROKER_URL = config("CELERY_BROKER", default="redis://redis:6379/1")
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True
CELERY_IMPORTS = [
    "common.emails",
    "common.utilities",
    "core.tasks",
    "video_requests.emails",
    "video_requests.utilities",
]
CELERY_TIMEZONE = config("TIME_ZONE", default="Europe/Budapest")

# One task per worker process. task_acks_late stays off: most tasks send emails
# or external notifications and aren't idempotent, so redelivery would double-send.
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Scheduled tasks
# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html

# Store schedule + last-run in the database, not a local shelve file, so beat
# works on a read-only root filesystem and survives pod restarts.
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_BEAT_SCHEDULE = {
    "update_request_status": {
        "task": "core.tasks.scheduled_update_request_status",
        "schedule": crontab(minute=10),
    },
    "daily_reminder_email": {
        "task": "core.tasks.scheduled_send_daily_reminder_email",
        "schedule": crontab(minute=0, hour=7),
    },
    "weekly_tasks_email": {
        "task": "core.tasks.scheduled_send_weekly_tasks_email",
        "schedule": crontab(minute=30, hour=0, day_of_week="mon"),
    },
    "unfinished_requests_email": {
        "task": "core.tasks.scheduled_send_unfinished_requests_email",
        "schedule": crontab(minute=0, hour=20, day_of_week="sun"),
    },
    # "overdue_requests_email": {
    #     "task": "core.tasks.scheduled_send_overdue_requests_email",
    #     "schedule": crontab(minute=30, hour=16, day_of_week="mon,wed,fri,sun"),
    # }, # TODO: Re-enable this later
    "cleaning": {
        "task": "core.tasks.scheduled_cleaning",
        "schedule": crontab(minute=30, hour=3),
    },
}

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# User authentication backends
# https://docs.djangoproject.com/en/6.0/ref/settings/#authentication-backends

AUTHENTICATION_BACKENDS = []
AUTH_USER_MODEL = "common.User"
ADMIN_GROUP = config("ADMIN_GROUP", default="Administrators")
SERVICE_ACCOUNTS_GROUP = config("SERVICE_ACCOUNTS_GROUP", default="Service Accounts")

# Django Rest Framework Settings
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "5/hour",
        "contact": "2/hour",
        "login": "5/minute",
    },
    "EXCEPTION_HANDLER": "common.rest_framework.exception.exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# Simple JWT Settings
# https://github.com/davesque/django-rest-framework-simplejwt

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=6),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGES = [
    ("en", _("English")),
    ("hu", _("Hungarian")),
]
LANGUAGE_CODE = config("LANGUAGE_CODE", default="en-us")
LOCALE_PATHS = [BACKEND_DIR / "locale"]
TIME_ZONE = config("TIME_ZONE", default="Europe/Budapest")
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATICFILES_DIRS = [
    FRONTEND_DIR / "build" / "static",
    FRONTEND_ADMIN_DIR / "build" / "static",
    BACKEND_DIR / "templates" / "static",
]
STATIC_ROOT = BACKEND_DIR / "staticfiles"
STATIC_URL = "/static/"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Whitenoise
# http://whitenoise.evans.io/en/stable/django.html

WHITENOISE_ROOT = FRONTEND_DIR / "build" / "root"

# Logging
# https://docs.djangoproject.com/en/6.0/topics/logging/

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(module)s | %(levelname)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "default",
        },
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "INFO"},
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "api.access": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# E-mail settings
# https://docs.djangoproject.com/en/6.0/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# Enable Django's admin site
DJANGO_ADMIN = config("DJANGO_ADMIN", default=True, cast=bool)
if DJANGO_ADMIN:
    # Enable Django admin
    INSTALLED_APPS += [
        "django.contrib.admin",
    ]

# Health check
# https://django-health-check.readthedocs.io/en/stable/
try:
    REDIS_URL = match(r"^rediss?://[\w.-]+:\d+", CACHEOPS_REDIS).group(0)
except AttributeError:
    raise ImproperlyConfigured("Cannot extract proper Redis URL from CACHE_REDIS.")

HEALTH_CHECK_URL_TOKEN = config("HEALTH_CHECK_URL_TOKEN", default=None)

# Full deep check for /health (dashboards, manual): everything.
HEALTH_CHECK_ENABLED_CHECKS = [
    "health_check.Cache",
    "health_check.Database",
    "health_check.Mail",
    "health_check.Storage",
    "health_check.contrib.celery.Ping",
    (
        "health_check.contrib.redis.Redis",
        {"client_factory": lambda: RedisClient.from_url(REDIS_URL)},
    ),
]

# Traffic-gating subset for /readyz: only DB and redis.
HEALTH_CHECK_READINESS_CHECKS = [
    "health_check.Database",
    (
        "health_check.contrib.redis.Redis",
        {"client_factory": lambda: RedisClient.from_url(REDIS_URL)},
    ),
]

# Cloudflare Turnstile
# https://developers.cloudflare.com/turnstile/

TURNSTILE_SECRET_KEY = config("TURNSTILE_SECRET_KEY", default=None)

# drf-spectacular
# https://drf-spectacular.readthedocs.io/en/latest/

SPECTACULAR_SETTINGS = {
    "COMPONENT_SPLIT_REQUEST": True,
    "CONTACT": {
        "email": "kecskemety.oliver@simonyi.bme.hu",
        "name": "Olivér Kecskeméty",
    },
    "DESCRIPTION": "REST API for Workflow Support System for managing video shooting, "
    "filming and live streaming requests of Budavári Schönherz Stúdió.",
    "SCHEMA_COERCE_PATH_PK_SUFFIX": True,
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVERS": [
        {
            "description": "Local development environment",
            "url": "http://localhost:8000",
        },
        {
            "description": "Production environment",
            "url": "https://felkeres.bsstudio.hu",
        },
        {
            "description": "Sandbox/staging environment",
            "url": "https://felkeres-dev.bsstudio.hu",
        },
    ],
    "TITLE": "BSS Request Manager API",
    "VERSION": "1.0.0",
}

SPECTACULAR_SERVE_SCHEMA = config("SPECTACULAR_SERVE_SCHEMA", default=False, cast=bool)
