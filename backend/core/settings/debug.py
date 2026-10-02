from datetime import timedelta

from core.settings._auth_social import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Enable local Django user based login
AUTHENTICATION_BACKENDS += ("django.contrib.auth.backends.ModelBackend",)

# Enable Browsable API
REST_FRAMEWORK.setdefault("DEFAULT_RENDERER_CLASSES", []).append(
    "rest_framework.renderers.BrowsableAPIRenderer"
)

# Enable CORS requests from anywhere
CORS_ALLOW_ALL_ORIGINS = True

# Local environment is not HTTPS
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Run Celery tasks synchronously in eager mode
# CELERY_TASK_ALWAYS_EAGER = True

# Enable Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]

# Do not send real e-mails
EMAIL_BACKEND_TYPE = config("EMAIL_BACKEND", default="console")
if EMAIL_BACKEND_TYPE.casefold() == "console":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
elif EMAIL_BACKEND_TYPE.casefold() == "file":
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = "logs/emails"

# Extend JWT access token lifetime
SIMPLE_JWT.update(
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(days=5),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=10),
    }
)

# Show debug output on the console
LOGGING["handlers"]["console"]["level"] = "DEBUG"
LOGGING["loggers"][""] = {"handlers": ["console"], "level": "DEBUG"}
