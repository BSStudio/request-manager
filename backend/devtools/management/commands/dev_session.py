import json
from importlib import import_module
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.core.management import BaseCommand, CommandError
from django.middleware.csrf import CSRF_SECRET_LENGTH
from django.utils.crypto import get_random_string

from api.v1.login.serializers import SessionUserSerializer
from common.models import User


class Command(BaseCommand):
    help = (
        "Print a browser login for a user, without OAuth, or write it as a "
        "Playwright storage state. Only the debug and test settings have this "
        "command."
    )

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "--storage-state",
            metavar="FILE",
            type=Path,
            help="Write the login to this file for Playwright instead of printing it.",
        )
        parser.add_argument(
            "--origin",
            default="https://localhost:5173",
            help="The site the storage state logs in to (default: %(default)s).",
        )

    def handle(self, *args, username, storage_state=None, origin, **options):
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
        # Only login() sets the CSRF cookie, and every write needs it.
        csrf_secret = get_random_string(CSRF_SECRET_LENGTH)

        if storage_state:
            write_storage_state(
                storage_state, origin, user, session.session_key, csrf_secret
            )
            self.stdout.write(f"Wrote the login of {username} to {storage_state}.")
            return

        self.stdout.write(
            "Paste this into the browser console on https://localhost:5173, logged "
            "out or in a private window (it cannot overwrite an existing login):\n"
        )
        # The frontend reads whether it is logged in from localStorage, and fills
        # in the rest of the user from /api/v1/me.
        self.stdout.write(
            f"document.cookie = '{settings.SESSION_COOKIE_NAME}="
            f"{session.session_key}; path=/'; "
            f"document.cookie = '{settings.CSRF_COOKIE_NAME}={csrf_secret}; path=/'; "
            f"localStorage.setItem('user_id', '{user.pk}'); location.reload();\n"
        )
        self.stdout.write(
            "The server must run with the same settings and .env, so that it reads "
            "this session store and uses the same secret key."
        )


def write_storage_state(
    path: Path, origin: str, user: User, session_key: str, csrf_secret: str
) -> None:
    domain = urlsplit(origin).hostname
    cookies = [
        cookie(
            settings.SESSION_COOKIE_NAME,
            session_key,
            domain,
            http_only=settings.SESSION_COOKIE_HTTPONLY,
            secure=settings.SESSION_COOKIE_SECURE,
            same_site=settings.SESSION_COOKIE_SAMESITE,
        ),
        cookie(
            settings.CSRF_COOKIE_NAME,
            csrf_secret,
            domain,
            http_only=settings.CSRF_COOKIE_HTTPONLY,
            secure=settings.CSRF_COOKIE_SECURE,
            same_site=settings.CSRF_COOKIE_SAMESITE,
        ),
    ]
    # The keys the frontend's setSession() writes after a real login.
    data = SessionUserSerializer(user).data
    local_storage = {
        "groups": json.dumps(data["groups"], ensure_ascii=False),
        "name": data["name"],
        "role": data["role"],
        "user_id": str(data["id"]),
    }
    if data["avatar_url"]:
        local_storage["avatar"] = data["avatar_url"]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cookies": cookies,
                "origins": [
                    {
                        "origin": origin,
                        "localStorage": [
                            {"name": name, "value": value}
                            for name, value in sorted(local_storage.items())
                        ],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def cookie(name, value, domain, *, http_only, secure, same_site):
    return {
        "name": name,
        "value": value,
        "domain": domain,
        "path": "/",
        "expires": -1,
        "httpOnly": http_only,
        "secure": secure,
        # Django's False leaves the attribute out, which browsers treat as Lax.
        "sameSite": same_site or "Lax",
    }
