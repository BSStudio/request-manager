from collections import defaultdict
from datetime import timedelta

from django.core.management import BaseCommand
from django.utils.timezone import now

from video_requests.emails import email_assignee_stale_todos
from video_requests.models import Todo

STALE_AFTER = timedelta(weeks=4)


class Command(BaseCommand):
    help = "Send each assignee their todos that have been open for four weeks or more"

    def handle(self, *args, **options):
        stale_todos = (
            Todo.objects.filter(
                status=Todo.Statuses.OPEN, created__lte=now() - STALE_AFTER
            )
            .select_related("request", "video__request")
            .prefetch_related("assignees")
            .order_by("created")
        )

        by_assignee = defaultdict(list)
        for todo in stale_todos:
            for assignee in todo.assignees.all():
                if assignee.is_staff:
                    by_assignee[assignee].append(todo)
        if not by_assignee:
            self.stdout.write(self.style.NOTICE("No assignee has a stale todo."))
            return

        for assignee, todos in by_assignee.items():
            email_assignee_stale_todos(assignee, todos)

        self.stdout.write(
            self.style.SUCCESS(
                f"Stale todos emails were sent to {len(by_assignee)} assignees."
            )
        )
