import json
import re
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command
from rest_framework.test import APIClient

from api.v1.login.serializers import SessionUserSerializer
from tests.factories import make_user

pytestmark = pytest.mark.django_db


def dev_session(username):
    with StringIO() as out:
        call_command("dev_session", username, stdout=out)
        return out.getvalue()


def test_the_printed_session_logs_the_user_in(client):
    user = make_user(username="someone")

    output = dev_session("someone")

    key = re.search(rf"{settings.SESSION_COOKIE_NAME}=(\w+)", output).group(1)
    client.cookies[settings.SESSION_COOKIE_NAME] = key
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    assert response.json()["id"] == user.pk
    assert f"localStorage.setItem('user_id', '{user.pk}')" in output


def test_the_printed_cookies_allow_writes():
    make_user(username="someone")
    output = dev_session("someone")
    client = APIClient(enforce_csrf_checks=True)
    for name in (settings.SESSION_COOKIE_NAME, settings.CSRF_COOKIE_NAME):
        match = re.search(rf"{name}=(\w+)", output)
        assert match, f"no {name} cookie in the snippet"
        client.cookies[name] = match.group(1)

    response = client.patch(
        "/api/v1/me",
        {"first_name": "Changed"},
        HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value,
    )

    assert response.status_code == 200


def test_an_unknown_user_is_an_error():
    with pytest.raises(CommandError, match="There is no user nobody"):
        dev_session("nobody")


def test_an_inactive_user_is_an_error():
    make_user(username="banned", banned=True)

    with pytest.raises(CommandError, match="inactive"):
        dev_session("banned")


def storage_state(username, path, **options):
    with StringIO() as out:
        call_command("dev_session", username, storage_state=path, stdout=out, **options)
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_storage_state_logs_the_user_in_and_allows_writes(tmp_path):
    user = make_user(username="someone")
    state = storage_state("someone", tmp_path / "someone.json")
    client = APIClient(enforce_csrf_checks=True)
    for cookie in state["cookies"]:
        client.cookies[cookie["name"]] = cookie["value"]

    assert client.get("/api/v1/me").json()["id"] == user.pk
    response = client.patch(
        "/api/v1/me",
        {"first_name": "Changed"},
        HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value,
    )
    assert response.status_code == 200


def test_the_storage_state_has_what_a_login_puts_in_local_storage(tmp_path):
    user = make_user(username="someone", groups=("Stáb",), avatar={})
    state = storage_state(
        "someone", tmp_path / "someone.json", origin="http://localhost:8010"
    )

    [origin] = state["origins"]
    data = SessionUserSerializer(user).data
    assert origin["origin"] == "http://localhost:8010"
    assert {item["name"]: item["value"] for item in origin["localStorage"]} == {
        "groups": '["Stáb"]',
        "name": data["name"],
        "role": data["role"],
        "user_id": str(user.pk),
    }
    assert {cookie["domain"] for cookie in state["cookies"]} == {"localhost"}


def test_the_storage_state_has_the_avatar_of_a_user_with_one(tmp_path):
    make_user(
        username="someone",
        avatar={"provider": "gravatar", "gravatar": "https://example.com/a.png"},
    )
    state = storage_state("someone", tmp_path / "someone.json")

    local_storage = {
        item["name"]: item["value"] for item in state["origins"][0]["localStorage"]
    }
    assert local_storage["avatar"] == "https://example.com/a.png"


def test_the_storage_state_is_not_written_for_an_inactive_user(tmp_path):
    make_user(username="banned", banned=True)

    with pytest.raises(CommandError, match="inactive"):
        storage_state("banned", tmp_path / "banned.json")
    assert not (tmp_path / "banned.json").exists()
