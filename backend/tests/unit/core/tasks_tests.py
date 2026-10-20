from datetime import timedelta

import pytest
from django.apps import apps
from django.utils import timezone
from model_bakery import baker

from core.tasks import scheduled_cleaning
from tests.factories import make_user
from video_requests.models import CrewMember, Todo

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
