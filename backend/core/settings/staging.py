import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import (
    LoggingIntegration,
    ignore_logger_for_events,
)
from sentry_sdk.integrations.redis import RedisIntegration

from common.sentry import EXCLUDED_BEAT_TASKS, before_send_log
from core.settings._auth_social import *

# Require an explicit secret key; base.py's random fallback differs per process
# and breaks sessions and CSRF across replicas and restarts.
SECRET_KEY = config("APP_SECRET_KEY")

# E-mail settings
# https://docs.djangoproject.com/en/6.0/topics/email/
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "logs/emails"

DEFAULT_REPLY_EMAIL = "reply@example.com"
WEEKLY_TASK_EMAIL = "weekly@example.com"

# External services:
SCH_EVENTS_TOKEN = "123456789abcdef"  # nosec

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
    disabled_integrations=[RedisIntegration()],
    dsn=config("SENTRY_URL"),
    integrations=[
        CeleryIntegration(
            exclude_beat_tasks=EXCLUDED_BEAT_TASKS, monitor_beat_tasks=True
        ),
        DjangoIntegration(cache_spans=False, middleware_spans=True),
        LoggingIntegration(event_level=logging.ERROR),
    ],
)
ignore_logger_for_events("django.security.DisallowedHost")
