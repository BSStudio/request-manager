from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.core import mail
from django.core.management import CommandError, call_command
from django.db.models import Count, F
from django.utils import timezone
from model_bakery import baker

from common.models import Ban, User
from tests.factories import make_user
from video_requests.models import (
    Comment,
    CrewMember,
    Project,
    Request,
    Todo,
    Video,
)

pytestmark = pytest.mark.django_db


def seed(**options):
    with StringIO() as out:
        call_command("seed_dev_data", interactive=False, stdout=out, **options)
        return out.getvalue()


def sso_user(username, **kwargs):
    """Somebody who logged in through single sign-on, so not at @example.com."""
    return make_user(username=username, email=f"{username}@bme.hu", **kwargs)


def counts():
    return [
        model.objects.count()
        for model in (User, Project, Request, Video, Comment, Todo)
    ]


def test_creates_the_people_in_their_roles():
    seed()

    assert User.objects.get(username="admin.aladar").is_admin
    assert "Főszerkesztő" in User.objects.get(username="szerk.szilvia").group_names
    assert User.objects.get(username="vago.vilma").is_staff
    assert not User.objects.get(username="minta.anna").is_staff
    banned = User.objects.get(username="tiltott.tamas")
    assert banned.is_banned
    assert not banned.is_active


def test_a_rerun_leaves_the_same_data():
    # The first rerun also creates the sentinel user: deleting the seeded admin
    # evaluates the SET() of their ban's creator, though the ban goes too.
    seed()
    seed()
    first = counts()

    seed()

    assert counts() == first


def test_keeps_sso_users_and_their_groups():
    user = sso_user("sso.user", groups=("Gyártásvezető",))

    seed()

    user.refresh_from_db()
    assert user.group_names == {"Gyártásvezető"}


def test_deletes_every_existing_request():
    request = baker.make(Request, requester=sso_user("sso.user"))
    baker.make(Video, request=request)

    seed()

    assert not Request.objects.filter(pk=request.pk).exists()


def test_deletes_every_existing_project():
    project = baker.make(Project, name="Régi projekt")

    seed()

    assert not Project.objects.filter(pk=project.pk).exists()


def test_creates_a_week_and_a_lecture_series(time_machine):
    # The lectures straddle the switch to winter time on 25 October.
    time_machine.move_to(datetime(2026, 10, 10, 12, tzinfo=ZoneInfo("Europe/Budapest")))
    seed()

    projects = Project.objects.annotate(request_count=Count("requests"))
    assert {project.name: project.request_count for project in projects} == {
        "Kollégiumi hét": 3,
        "Fizika 1 előadások": 4,
    }
    starts = [
        timezone.localtime(start)
        for start in Request.objects.filter(project__name="Fizika 1 előadások")
        .order_by("start_datetime")
        .values_list("start_datetime", flat=True)
    ]
    days = [start.date() for start in starts]
    assert [later - earlier for earlier, later in zip(days, days[1:])] == [
        timedelta(weeks=1)
    ] * 3
    assert {start.hour for start in starts} == {10}


def test_deletes_requests_that_no_longer_validate():
    request = baker.make(Request)
    baker.make(Video, request=request)
    Request.objects.filter(pk=request.pk).update(
        deadline=request.end_datetime.date() - timedelta(days=1)
    )

    seed()

    assert not Request.objects.filter(pk=request.pk).exists()


def test_replaces_leftover_users_with_a_seed_username():
    make_user(username="minta.anna", email="anna@old-script.test")

    seed()

    assert User.objects.get(username="minta.anna").email == "minta.anna@example.com"


def test_a_ban_made_by_a_seeded_admin_survives_a_rerun():
    seed()
    user = sso_user("sso.user")
    Ban.objects.create(receiver=user, creator=User.objects.get(username="admin.aladar"))

    seed()

    user.refresh_from_db()
    assert user.is_banned
    assert not user.is_active


def test_cancelling_at_the_prompt_changes_nothing(monkeypatch):
    request = baker.make(Request, requester=sso_user("sso.user"))
    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    with StringIO() as out:
        call_command("seed_dev_data", stdout=out)
        output = out.getvalue()

    assert "Nothing was changed." in output
    assert Request.objects.filter(pk=request.pk).exists()
    assert not User.objects.filter(username="admin.aladar").exists()


def test_answering_yes_seeds(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "yes")

    call_command("seed_dev_data", stdout=StringIO())

    assert User.objects.filter(username="admin.aladar").exists()


def test_seeding_sends_no_mail_and_queues_no_task(django_capture_on_commit_callbacks):
    with patch("celery.app.task.Task.apply_async") as apply_async:
        with django_capture_on_commit_callbacks(execute=True):
            seed()

    apply_async.assert_not_called()
    assert mail.outbox == []


def test_every_run_creates_the_same_data():
    def snapshot():
        return sorted(
            Request.objects.values_list(
                "title", "status", "start_datetime", "requester__username"
            )
        )

    seed()
    first = snapshot()

    seed()

    assert snapshot() == first


def test_me_gets_requests_crew_spots_a_video_and_todos():
    me = sso_user("me.sso")

    seed(me="me.sso")

    assert set(
        Request.objects.filter(requester=me).values_list("status", flat=True)
    ) == {Request.Statuses.REQUESTED, Request.Statuses.ACCEPTED, Request.Statuses.DONE}
    assert Request.objects.filter(requester=me).count() == 3
    assert CrewMember.objects.filter(member=me).count() == 2
    assert Video.objects.filter(editor=me).count() == 1
    assert Todo.objects.filter(assignees=me).count() == 2


def test_me_leaves_the_other_requests_as_they_are():
    def others():
        return sorted(
            Request.objects.exclude(requester__username="me.sso").values_list(
                "title", "status", "requester__username"
            )
        )

    sso_user("me.sso")
    seed()
    without_me = others()

    seed(me="me.sso")

    assert others() == without_me


def test_me_can_be_a_seeded_user():
    seed(me="minta.anna")

    assert Todo.objects.filter(assignees__username="minta.anna").count() == 2


def test_an_unknown_me_changes_nothing():
    request = baker.make(Request, requester=sso_user("sso.user"))

    with pytest.raises(CommandError, match="Log in with that account once"):
        seed(me="nobody")

    assert Request.objects.filter(pk=request.pk).exists()


def test_me_sends_no_mail_and_queues_no_task(django_capture_on_commit_callbacks):
    sso_user("me.sso")

    with patch("celery.app.task.Task.apply_async") as apply_async:
        with django_capture_on_commit_callbacks(execute=True):
            seed(me="me.sso")

    apply_async.assert_not_called()
    assert mail.outbox == []


def test_requests_were_submitted_before_their_events_and_messages():
    seed(me="minta.anna")

    assert not Request.objects.filter(
        start_datetime__lt=timezone.now(), created__gte=F("start_datetime")
    ).exists()
    assert not Comment.objects.filter(created__lt=F("request__created")).exists()
