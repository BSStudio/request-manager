from importlib import import_module

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.core.management import BaseCommand, CommandError

from common.models import User


class Command(BaseCommand):
    help = (
        "Print a browser login for a user, without OAuth. "
        "Only the debug and test settings have this command."
    )

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, username, **options):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"There is no user {username}.")
        if not user.is_active:
            raise CommandError(
                f"{username} is inactive, banned for example, so it cannot log in."
            )

        session = import_module(settings.SESSION_ENGINE).SessionStore()
        session[SESSION_KEY] = user._meta.pk.value_to_string(user)
        session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.create()

        self.stdout.write(
            "Paste this into the browser console on https://localhost:5173, logged "
            "out or in a private window (it cannot overwrite an existing login):\n"
        )
        # The frontend reads whether it is logged in from localStorage, and fills
        # in the rest of the user from /api/v1/me.
        self.stdout.write(
            f"document.cookie = '{settings.SESSION_COOKIE_NAME}="
            f"{session.session_key}; path=/'; "
            f"localStorage.setItem('user_id', '{user.pk}'); location.reload();\n"
        )
        self.stdout.write(
            "The server must run with the same settings and .env, so that it reads "
            "this session store and uses the same secret key."
        )
