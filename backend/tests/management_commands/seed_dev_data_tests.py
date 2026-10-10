from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from model_bakery import baker

from common.models import Ban, User
from tests.factories import make_user
from video_requests.models import Comment, Request, Todo, Video

pytestmark = pytest.mark.django_db


def seed(**options):
    with StringIO() as out:
        call_command("seed_dev_data", interactive=False, stdout=out, **options)
        return out.getvalue()


def sso_user(username, **kwargs):
    """Somebody who logged in through single sign-on, so not at @example.com."""
    return make_user(username=username, email=f"{username}@bme.hu", **kwargs)


def counts():
    return [model.objects.count() for model in (User, Request, Video, Comment, Todo)]


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
