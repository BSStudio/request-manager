from datetime import timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from common.models import get_sentinel_user
from common.utilities import (
    create_calendar_event,
    get_google_calendar_service,
    remove_calendar_event,
    update_calendar_event,
)
from video_requests.models import Request


class Command(BaseCommand):
    help = "Test Google Calendar API"

    def add_arguments(self, parser):
        parser.add_argument(
            "-l",
            "--list",
            action="store_true",
            help="List available calendars for service account.",
        )
        parser.add_argument(
            "-c", "--check", type=str, help="Check if this calendar is available."
        )
        parser.add_argument(
            "-a", "--accept", type=str, help="Accept invitation for given calendar."
        )
        parser.add_argument(
            "-rm", "--remove", type=str, help="Remove calendar from service account."
        )
        parser.add_argument(
            "-t",
            "--test",
            action="store_true",
            help="Save a test event to the calendar.",
        )

    def handle(self, *args, **options):
        ls = options["list"]
        check = options["check"]
        accept = options["accept"]
        remove = options["remove"]
        test = options["test"]

        service = get_google_calendar_service()

        if ls or check:
            calendar_list = service.calendarList().list().execute()
            if calendar_list["items"]:
                for event in calendar_list["items"]:
                    if ls:
                        self.stdout.write(
                            self.style.SUCCESS(f'{event["summary"]} - {event["id"]}')
                        )
                    elif check:
                        if event["id"] == check:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    "Service account has access to the calendar."
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(
                                    "Service account does not have access to the calendar."
                                )
                            )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "Service account does not have access to any calendars."
                    )
                )

        elif accept:
            event = {"id": accept}
            service.calendarList().insert(body=event).execute()
            self.stdout.write(
                self.style.SUCCESS(
                    "Calendar was added to service account successfully."
                )
            )

        elif remove:
            service.calendarList().delete(calendarId=remove).execute()
            self.stdout.write(
                self.style.SUCCESS(
                    "Calendar was removed from service account successfully."
                )
            )

        elif test:
            start = timezone.now()
            request = Request.objects.create(
                title="Google Calendar API test",
                start_datetime=start,
                end_datetime=start + timedelta(hours=2),
                place="Test place",
                type="Test type",
                requester=get_sentinel_user(),
                requested_by=get_sentinel_user(),
            )
            try:
                # Which credential file are we using
                self.stdout.write("----------- Key file path -----------")
                self.stdout.write(settings.GOOGLE_SERVICE_ACCOUNT_KEY_FILE_PATH)
                # Create the event
                self.stdout.write("----------- Creating new event -----------")
                self.stdout.write("The event will be created for today.")
                self.stdout.write(
                    "It should contain: title, description, place, start and end datetime."
                )
                create_calendar_event(request.id)
                self.stdout.write(self.style.SUCCESS("Event was saved successfully."))
                input("Check and validate the calendar and press Enter to continue...")

                # Change some data and update the event
                self.stdout.write("----------- Updating the event -----------")
                self.stdout.write("The event should be shifted one day forward.")
                self.stdout.write(
                    "The following fields should be updated: title, place, start and end datetime."
                )
                request.refresh_from_db()  # Refresh the object to contain calendar_id
                request.title = "Changed title"
                request.place = "Changed place"
                request.end_datetime = request.end_datetime + timedelta(days=1)
                request.start_datetime = request.start_datetime + timedelta(days=1)
                request.save()
                update_calendar_event(request.id)
                self.stdout.write(self.style.SUCCESS("Event was updated successfully."))
                input("Check and validate the calendar and press Enter to continue...")

                # Delete the event from the calendar
                self.stdout.write("----------- Deleting the event -----------")
                remove_calendar_event(request.id)
                self.stdout.write(
                    self.style.SUCCESS(
                        "Event was deleted successfully. Check the calendar."
                    )
                )
            finally:
                request.delete()

        else:
            self.stdout.write(
                self.style.ERROR("Please define exactly one argument or flag.")
            )
