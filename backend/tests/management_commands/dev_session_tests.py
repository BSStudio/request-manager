import re
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command
from rest_framework.test import APIClient

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
