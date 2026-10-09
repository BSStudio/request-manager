from datetime import timedelta

from django.core.management import BaseCommand
from django.utils.timezone import localdate

from video_requests.emails import email_staff_weekly_tasks
from video_requests.models import Request, Video


class Command(BaseCommand):
    help = "Send email about task to do this week"

    def handle(self, *args, **options):
        # Get requests which will happen this week
        date = localdate()
        start_week = date - timedelta(date.weekday())
        end_week = start_week + timedelta(7)
        recording = (
            Request.objects.filter(
                start_datetime__date__range=[start_week, end_week],
                status__range=[1, 2],
            )
            .order_by("start_datetime")
            .prefetch_related("crew__member")
        )

        # Get requests which are already recorded but no video was created yet
        recorded_requests_without_video = Request.objects.filter(
            status__range=[3, 4], videos__isnull=True
        )
        # Get videos having requests already recorded but editing is not finished yet
        unedited_videos = Video.objects.filter(
            request__status__range=[3, 4], status__range=[1, 2]
        ).select_related("request", "editor")

        # Send the email if any of the queries contains data
        if (
            recording.exists()
            or recorded_requests_without_video.exists()
            or unedited_videos.exists()
        ):
            email_staff_weekly_tasks(
                recording, recorded_requests_without_video, unedited_videos
            )
            self.stdout.write(
                self.style.SUCCESS("Weekly tasks email was sent successfully.")
            )
        else:
            self.stdout.write(self.style.NOTICE("No tasks for this week."))
