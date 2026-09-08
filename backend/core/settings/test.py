from datetime import timedelta

from core.settings._auth_social import *

# Use localhost as default instead of docker container hostnames
DATABASES["default"].update({"HOST": config("DATABASE_HOST", default="localhost")})
CACHEOPS_REDIS = config("CACHE_REDIS", default="redis://localhost:6379/0")
CELERY_BROKER_URL = config("CELERY_BROKER", default="redis://localhost:6379/1")

# Use the default Django authentication backend
AUTHENTICATION_BACKENDS += ["django.contrib.auth.backends.ModelBackend"]

# Test environment is not HTTPS
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

# AuthSCH OAuth2 settings:
SOCIAL_AUTH_AUTHSCH_KEY = "12345678901234567890"  # nosec
SOCIAL_AUTH_AUTHSCH_SECRET = "TNcJ3UoBMUqpfYLBqlGlqN0Lsw1LHyIFvEtMTatL65RtTKAc6JnAYyNdDHX2DLFxkWLHpef8Wu8GHIAr"  # nosec

# BSS Login OAuth2 settings:
AUTH_BSS_CLIENT_ID = "DrOiL0kPpOgCdsMuNe07W7YH83vN20TGuxTdcb26"  # nosec
AUTH_BSS_CLIENT_SECRET = "kFIVw4i1oLScJczZN2hebatRsS8APPwoe8JpUWb93JlZ4TZJw7ZlWihAlOnv5xwtQRsjEUj668u12uCmzfVkjOCH3mBfU7MUlE3uJX8EZ1TzxTgR9oPYr4gHJu9KIhFn"  # nosec
# Set on the names the pipeline reads. AUTH_BSS_* only reaches the settings
# through the environment, which CI does not provide.
SOCIAL_AUTH_BSS_LOGIN_SUPERUSER_GROUP = "Admin"
SOCIAL_AUTH_BSS_LOGIN_EXCLUDE_GROUPS = ["Admin"]

# Google OAuth2 settings:
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = (
    "123456789012-p95xsuczae7s1w8un1apct2c90s6rj19.apps.googleusercontent.com"  # nosec
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "27c7dFrK6aYsuvHLmV5Be3zU"  # nosec

# Microsoft OAuth2 settings:
SOCIAL_AUTH_MICROSOFT_GRAPH_KEY = "9cf7a0de-7bb8-0bd1-ec3a-925173e652ee"  # nosec
SOCIAL_AUTH_MICROSOFT_GRAPH_SECRET = "FYT8Q~pV~qBOa0jEr9N8yf0qOa7yPnZa1xf1daNF"  # nosec

# Model Bakery
# https://model-bakery.readthedocs.io/en/latest/how_bakery_behaves.html
BAKER_CUSTOM_FIELDS_GEN = {
    "phonenumber_field.modelfields.PhoneNumberField": "tests.helpers.baker_generators.gen_phone_number",
}

# Use faster password hashing algorithm
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Do not search for frontend build for tests
STATICFILES_DIRS.pop(0)
WHITENOISE_ROOT = None

# Override admin group to use the default value for tests
ADMIN_GROUP = "Administrators"

# Use short lifetime on access tokens
SIMPLE_JWT.update({"ACCESS_TOKEN_LIFETIME": timedelta(seconds=10)})

# Increase the throttling rates
REST_FRAMEWORK.update(
    {
        "DEFAULT_THROTTLE_RATES": {
            "anon": "500000/second",
            "contact": "500000/second",
            "login": "500000/second",
        }
    }
)

# Disable caching
CACHEOPS_ENABLED = False

# Save celery result to database when running in eager mode
CELERY_TASK_STORE_EAGER_RESULT = True

# Do not send real e-mails
EMAIL_BACKEND_LIST = [
    "django.core.mail.backends.filebased.EmailBackend",
    "django.core.mail.backends.locmem.EmailBackend",
]
EMAIL_FILE_PATH = "logs/emails"
DEFAULT_REPLY_EMAIL = "reply@example.com"
WEEKLY_TASK_EMAIL = "weekly@example.com"

# Do not create real calendar events
GOOGLE_CALENDAR_ID = "NOT_EXISTING"
GOOGLE_SERVICE_ACCOUNT_KEY_FILE_PATH = None

# Random external token
SCH_EVENTS_TOKEN = "123456789abcdef"  # nosec

# Remove celery and update Redis health check to use the local REDIS_URL
try:
    REDIS_URL = match(r"^rediss?://[\w.-]+:\d+", CACHEOPS_REDIS).group(0)
except AttributeError:
    raise ImproperlyConfigured("Cannot extract proper Redis URL from CACHE_REDIS.")

HEALTH_CHECK_ENABLED_CHECKS = [
    check
    for check in HEALTH_CHECK_ENABLED_CHECKS
    if check != "health_check.contrib.celery.Ping"
    and not (isinstance(check, tuple) and "Redis" in check[0])
] + [
    (
        "health_check.contrib.redis.Redis",
        {"client_factory": lambda: RedisClient.from_url(REDIS_URL)},
    ),
]

HEALTH_CHECK_READINESS_CHECKS = [
    check
    for check in HEALTH_CHECK_READINESS_CHECKS
    if not (isinstance(check, tuple) and "Redis" in check[0])
] + [
    (
        "health_check.contrib.redis.Redis",
        {"client_factory": lambda: RedisClient.from_url(REDIS_URL)},
    ),
]

# Set Cloudflare Turnstile to test mode
TURNSTILE_TESTING = True

# Disable file logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
