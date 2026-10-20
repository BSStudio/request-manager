from io import StringIO

from celery import shared_task
from django.apps import apps
from django.core.management import call_command


@shared_task
def scheduled_sync_bss_users():
    with StringIO() as out:
        call_command("sync_bss_users", stdout=out)
        return out.getvalue()


@shared_task
def scheduled_update_request_status():
    with StringIO() as out:
        call_command("update_request_status", stdout=out)
        return out.getvalue()


@shared_task
def scheduled_send_daily_reminder_email():
    with StringIO() as out:
        call_command("email_daily_reminders", stdout=out)
        return out.getvalue()


@shared_task
def scheduled_send_weekly_tasks_email():
    with StringIO() as out:
        call_command("email_weekly_tasks", stdout=out)
        return out.getvalue()


@shared_task
def scheduled_send_unfinished_requests_email():
    with StringIO() as out:
        call_command("email_unfinished_requests", stdout=out)
        return out.getvalue()


@shared_task
def scheduled_send_overdue_requests_email():
    with StringIO() as out:
        call_command("email_overdue_requests", stdout=out)
        return out.getvalue()


@shared_task
def scheduled_send_stale_todos_email():
    with StringIO() as out:
        call_command("email_stale_todos", stdout=out)
        return out.getvalue()


@shared_task
def scheduled_cleaning():
    with StringIO() as out:
        call_command(
            "clean_duplicate_history", "--minutes", "1500", auto=True, stdout=out
        )
        call_command(
            "clean_old_history",
            "video_requests.Comment",
            "video_requests.CrewMember",
            "video_requests.Rating",
            "video_requests.Todo",
            "--days",
            "90",
            stdout=out,
        )
        # The assignees recorded with a todo version must go with it, but
        # clean_old_history leaves them behind.
        HistoricalTodo = apps.get_model("video_requests", "HistoricalTodo")
        apps.get_model("video_requests", "HistoricalTodo_assignees").objects.exclude(
            history__in=HistoricalTodo.objects.all()
        ).delete()
        return out.getvalue()
