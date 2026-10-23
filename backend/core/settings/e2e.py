from core.settings.test import *

# Only these settings let e2e_server drop and recreate the database.
E2E = True

DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Its own test database, so pytest's test_… database and the dev database are
# never touched.
DATABASES["default"].update(
    {"NAME": "request_manager_e2e", "TEST": {"NAME": "request_manager_e2e"}}
)

# Serve the frontend build as in production, which test.py turns off. Served
# straight from frontend/build, so no collectstatic.
STATICFILES_DIRS.insert(0, FRONTEND_DIR / "build" / "static")
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}
# The Docker image moves the root files (manifest, icons, sw.js) into build/root.
WHITENOISE_ROOT = FRONTEND_DIR / "build"
WHITENOISE_USE_FINDERS = True

# Shows the push switches. Nothing is ever sent: the tests block service
# workers, so no browser subscribes.
WEB_PUSH_CONTACT = "mailto:e2e@example.com"
WEB_PUSH_VAPID_PRIVATE_KEY = "e2e"
WEB_PUSH_VAPID_PUBLIC_KEY = "e2e"

# E-mail tasks run in the request, so a broken template fails the test, and
# neither Redis nor a worker is needed.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
