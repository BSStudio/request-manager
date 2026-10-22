from datetime import timedelta

import pytest
from django.apps import apps
from django.contrib.sessions.models import Session
from django.utils import timezone
from model_bakery import baker

from core.tasks import scheduled_cleaning
from tests.factories import make_user
from video_requests.models import CrewMember, Notification, Todo

pytestmark = pytest.mark.django_db


def test_cleaning_drops_crew_and_todo_history_older_than_90_days():
    crew_member = baker.make("video_requests.CrewMember", position="Operatőr")
    todo = baker.make("video_requests.Todo", description="Cut the trailer")
    todo.assignees.add(make_user(username="assignee"))
    long_ago = timezone.now() - timedelta(days=91)
    CrewMember.history.update(history_date=long_ago)
    Todo.history.update(history_date=long_ago)
    crew_member.position = "Rendező"
    crew_member.save()
    todo.description = "Cut the teaser"
    todo.save()

    scheduled_cleaning()

    assert [record.position for record in CrewMember.history.all()] == ["Rendező"]
    assert [record.description for record in Todo.history.all()] == ["Cut the teaser"]
    assignees = apps.get_model("video_requests", "HistoricalTodo_assignees")
    assert list(assignees.objects.values_list("history", flat=True)) == [
        Todo.history.get().history_id
    ]


def test_cleaning_drops_expired_sessions():
    now = timezone.now()
    Session.objects.create(
        session_key="expired", session_data="", expire_date=now - timedelta(days=1)
    )
    Session.objects.create(
        session_key="active", session_data="", expire_date=now + timedelta(days=1)
    )

    scheduled_cleaning()

    assert list(Session.objects.values_list("session_key", flat=True)) == ["active"]


def test_cleaning_drops_notifications_older_than_30_days():
    now = timezone.now()
    old, recent = baker.make("video_requests.Notification", _quantity=2)
    # created is auto_now_add, so it can only be moved after the insert.
    Notification.objects.filter(pk=old.pk).update(created=now - timedelta(days=31))
    Notification.objects.filter(pk=recent.pk).update(created=now - timedelta(days=29))

    scheduled_cleaning()

    assert list(Notification.objects.values_list("pk", flat=True)) == [recent.pk]
