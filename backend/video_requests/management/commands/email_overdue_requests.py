from collections import defaultdict

from django.core.management import BaseCommand
from django.utils.timezone import localdate

from video_requests.emails import (
    email_responsible_overdue_requests,
    email_staff_overdue_requests,
)
from video_requests.models import Request


class Command(BaseCommand):
    help = (
        "Send each responsible their requests whose videos are overdue, "
        "and the editor in chief and production managers all of them"
    )

    def handle(self, *args, **options):
        overdue_requests = list(
            Request.objects.filter(
                status__range=[Request.Statuses.RECORDED, Request.Statuses.UPLOADED],
                deadline__lt=localdate(),
            )
            .select_related("responsible")
            .order_by("deadline")
        )
        if not overdue_requests:
            self.stdout.write(self.style.NOTICE("No overdue request was found."))
            return

        by_responsible = defaultdict(list)
        for request in overdue_requests:
            if request.responsible and request.responsible.is_staff:
                by_responsible[request.responsible].append(request)
        for responsible, requests in by_responsible.items():
            email_responsible_overdue_requests(responsible, requests)
        email_staff_overdue_requests(overdue_requests)

        self.stdout.write(
            self.style.SUCCESS(
                f"Overdue requests emails were sent: {len(overdue_requests)} requests, "
                f"{len(by_responsible)} responsibles."
            )
        )
