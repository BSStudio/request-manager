import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import (
    LoggingIntegration,
    ignore_logger_for_events,
)
from sentry_sdk.integrations.redis import RedisIntegration

from common.sentry import EXCLUDED_BEAT_TASKS, before_send_log, traces_sampler
from core.settings._auth_social import *

# Require an explicit secret key; base.py's random fallback differs per process
# and breaks sessions and CSRF across replicas and restarts.
SECRET_KEY = config("APP_SECRET_KEY")

# E-mail settings
# https://docs.djangoproject.com/en/6.0/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT")

EMAIL_HOST_USER = config("EMAIL_HOST_USER", default=None)
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default=None)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=None)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=None)
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", default=None)
EMAIL_SSL_KEYFILE = config("EMAIL_SSL_KEYFILE", default=None)
EMAIL_SSL_CERTFILE = config("EMAIL_SSL_CERTFILE", default=None)

DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
DEFAULT_REPLY_EMAIL = config("DEFAULT_REPLY_EMAIL")
WEEKLY_TASK_EMAIL = config("WEEKLY_TASK_EMAIL")

# External services:
SCH_EVENTS_TOKEN = config("SCH_EVENTS_TOKEN")

# Google Calendar settings:
GOOGLE_SERVICE_ACCOUNT_KEY_FILE_NAME = config("GOOGLE_SERVICE_ACCOUNT_KEY_FILE_NAME")
GOOGLE_SERVICE_ACCOUNT_KEY_FILE_PATH = (
    f"credentials/{GOOGLE_SERVICE_ACCOUNT_KEY_FILE_NAME}"
)
GOOGLE_CALENDAR_ID = config("GOOGLE_CALENDAR_ID")

# Sentry (collect unhandled errors and exceptions and sends reports)
# https://sentry.io

sentry_sdk.init(
    before_send_log=before_send_log,
    data_collection=SENTRY_DATA_COLLECTION,
    # It records Redis keys, and the session cache keys are the session IDs.
    disabled_integrations=[RedisIntegration()],
    dsn=config("SENTRY_URL"),
    integrations=[
        CeleryIntegration(
            exclude_beat_tasks=EXCLUDED_BEAT_TASKS, monitor_beat_tasks=True
        ),
        # Its cache spans are named after the cache keys too.
        DjangoIntegration(cache_spans=False, middleware_spans=True),
        # Logs and breadcrumbs from INFO, the default; events only from ERROR.
        LoggingIntegration(event_level=logging.ERROR),
    ],
    traces_sampler=traces_sampler,
)
ignore_logger_for_events("django.security.DisallowedHost")
