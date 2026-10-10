from core.settings._auth_social import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Fixed, unlike base.py's random key per process: sessions survive a restart, and
# the ones dev_session creates in its own process verify on the server.
SECRET_KEY = config("APP_SECRET_KEY", default="django-insecure-request-manager-dev")

# Enable local Django user based login
AUTHENTICATION_BACKENDS += ("django.contrib.auth.backends.ModelBackend",)

# Test data commands; production settings never install them.
INSTALLED_APPS += ["devtools"]

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

# Except through the frontend dev server, which proxies the API and sets this
# header, so CSRF and OAuth redirect URIs see its https://localhost:5173 origin.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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

# Show debug output on the console
LOGGING["handlers"]["console"]["level"] = "DEBUG"
LOGGING["loggers"][""] = {"handlers": ["console"], "level": "DEBUG"}
