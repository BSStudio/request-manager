from django.core.management import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Q
from django.db.models.signals import post_delete

from common.models import User
from devtools.bulk import create_bulk
from devtools.me import attach_to
from devtools.people import EMAIL_DOMAIN, PEOPLE, create_people
from devtools.scenarios import create_scenarios
from video_requests.models import Request, Video
from video_requests.signals import update_request_status_after_video_delete


class Command(BaseCommand):
    help = (
        "Replace every request and every test user with fresh test data. "
        "Only the debug and test settings have this command."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--me",
            metavar="USERNAME",
            help="Also give this user requests, crew spots, a video to edit and todos.",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do not ask for confirmation.",
        )

    def handle(self, *args, me=None, interactive=True, **options):
        if interactive and not self.confirm():
            self.stdout.write("Nothing was changed.")
            return

        with transaction.atomic():
            delete_seed_data()
            people = create_people()
            scenarios = create_scenarios(people)
            create_bulk(people)
            if me:
                # Looked up only now: --me may name one of the people just created.
                attach_to(find_user(me), people, scenarios)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Request.objects.count()} requests for "
                f"{User.objects.filter(email__endswith=f'@{EMAIL_DOMAIN}').count()} "
                "people."
            )
        )
        self.stdout.write(
            "Log in as the admin with: python manage.py dev_session admin.aladar"
        )

    def confirm(self) -> bool:
        database = connection.settings_dict
        answer = input(
            f"This deletes every request in the {database['NAME']} database on "
            f"{database['HOST']}, and every user with an @{EMAIL_DOMAIN} address.\n"
            "Type 'yes' to continue, or anything else to cancel: "
        )
        return answer == "yes"


def find_user(username: str) -> User:
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        raise CommandError(
            f"There is no user {username}. "
            "Log in with that account once, then run this again."
        )


def delete_seed_data() -> None:
    # Deleting a video saves its request with a recalculated status, which raises
    # for a request that no longer validates, and the request goes anyway.
    post_delete.disconnect(update_request_status_after_video_delete, sender=Video)
    try:
        Request.objects.all().delete()
    finally:
        post_delete.connect(update_request_status_after_video_delete, sender=Video)
    User.objects.filter(
        Q(email__endswith=f"@{EMAIL_DOMAIN}")
        | Q(username__in=[person.username for person in PEOPLE])
    ).delete()
