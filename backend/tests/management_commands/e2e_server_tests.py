import json
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command
from django.db import connection

from common.models import User
from devtools.people import EMAIL_DOMAIN, PEOPLE
from tests.factories import make_user

pytestmark = pytest.mark.django_db


def e2e_server(*args, **options):
    with (
        patch.object(connection.creation, "create_test_db") as create_test_db,
        patch("devtools.management.commands.e2e_server.serve") as serve,
        StringIO() as out,
    ):
        call_command("e2e_server", *args, stdout=out, **options)
    return create_test_db, serve


def test_it_refuses_to_run_without_the_e2e_settings(tmp_path):
    with pytest.raises(CommandError, match="core.settings.e2e"):
        e2e_server(storage_state_dir=tmp_path)
    assert not list(tmp_path.iterdir())


def test_it_recreates_the_database_seeds_and_serves(settings, tmp_path):
    settings.E2E = True

    create_test_db, serve = e2e_server("localhost:8123", storage_state_dir=tmp_path)

    create_test_db.assert_called_once_with(
        verbosity=1, autoclobber=True, serialize=False, keepdb=False
    )
    usernames = [person.username for person in PEOPLE]
    assert User.objects.filter(username__in=usernames).count() == len(PEOPLE)
    serve.assert_called_once_with("localhost:8123")


def test_it_writes_a_login_for_every_active_seeded_user(settings, tmp_path):
    settings.E2E = True
    make_user(username="sso.user")

    e2e_server("localhost:8123", storage_state_dir=tmp_path)

    active = set(
        User.objects.filter(
            email__endswith=f"@{EMAIL_DOMAIN}", is_active=True
        ).values_list("username", flat=True)
    )
    assert {path.stem for path in tmp_path.glob("*.json")} == active
    assert "tiltott.tamas" not in active
    state = json.loads((tmp_path / "minta.anna.json").read_text(encoding="utf-8"))
    assert state["origins"][0]["origin"] == "http://localhost:8123"
