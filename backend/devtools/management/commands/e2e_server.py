from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection

from common.models import User
from devtools.people import EMAIL_DOMAIN


class Command(BaseCommand):
    help = (
        "Recreate the E2E database with fresh test data, write a Playwright login "
        "for every test user, then serve the app. Only for core.settings.e2e."
    )

    def add_arguments(self, parser):
        parser.add_argument("addrport", nargs="?", default="localhost:8010")
        parser.add_argument(
            "--storage-state-dir",
            metavar="DIR",
            type=Path,
            help="Write <username>.json logins for Playwright into this directory.",
        )

    def handle(self, *args, addrport, storage_state_dir=None, **options):
        if not getattr(settings, "E2E", False):
            raise CommandError(
                "This drops the database, so it only runs with "
                "DJANGO_SETTINGS_MODULE=core.settings.e2e."
            )

        connection.creation.create_test_db(
            verbosity=1, autoclobber=True, serialize=False, keepdb=False
        )
        call_command("seed_dev_data", interactive=False, stdout=self.stdout)

        if storage_state_dir:
            users = User.objects.filter(
                email__endswith=f"@{EMAIL_DOMAIN}", is_active=True
            )
            for username in users.values_list("username", flat=True):
                call_command(
                    "dev_session",
                    username,
                    storage_state=storage_state_dir / f"{username}.json",
                    origin=f"http://{addrport}",
                    stdout=self.stdout,
                )

        serve(addrport)


def serve(addrport: str) -> None:
    # Without the reloader, so a single process owns the database.
    call_command("runserver", addrport, use_reloader=False)
