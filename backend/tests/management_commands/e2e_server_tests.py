import json
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command
from django.db import connection

from common.models import User
from devtools.management.commands.e2e_server import serve
from devtools.people import PEOPLE
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
    with (
        patch.object(connection.creation, "create_test_db") as create_test_db,
        patch("devtools.management.commands.e2e_server.serve") as serve,
        pytest.raises(CommandError, match="core.settings.e2e"),
    ):
        call_command("e2e_server", storage_state_dir=tmp_path)

    create_test_db.assert_not_called()
    serve.assert_not_called()
    assert not list(tmp_path.iterdir())


def test_it_recreates_the_database_seeds_and_serves(settings, tmp_path):
    settings.E2E = True

    create_test_db, serve = e2e_server("localhost:8123", storage_state_dir=tmp_path)

    create_test_db.assert_called_once_with(verbosity=1, autoclobber=True, keepdb=False)
    usernames = [person.username for person in PEOPLE]
    assert User.objects.filter(username__in=usernames).count() == len(PEOPLE)
    serve.assert_called_once_with("localhost:8123")


def test_it_writes_logins_only_for_active_seeded_users(settings, tmp_path):
    settings.E2E = True
    make_user(username="sso.user", email="sso.user@sch.bme.hu")

    e2e_server("localhost:8123", storage_state_dir=tmp_path)

    written = {path.stem for path in tmp_path.glob("*.json")}
    assert {"admin.aladar", "minta.anna", "ures.peter"} <= written
    assert not {"sso.user", "tiltott.tamas"} & written
    state = json.loads((tmp_path / "minta.anna.json").read_text(encoding="utf-8"))
    assert state["origins"][0]["origin"] == "http://localhost:8123"


def test_it_serves_without_the_reloader():
    with patch("devtools.management.commands.e2e_server.call_command") as command:
        serve("localhost:8123")

    command.assert_called_once_with("runserver", "localhost:8123", use_reloader=False)
