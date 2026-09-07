import logging

import pytest
import responses
from django.core.management import call_command

from common.models import User
from tests.helpers.users_test_utils import create_user

SYNC_URL = "https://login.bsstudio.hu/api/v3/core/users/?is_active=true&page_size=1000&path=users&type=internal"

COMPLETE_ATTRIBUTES = {
    "first_name": "Test",
    "last_name": "User",
    "mobile": "+36701234567",
}


def directory_user(username, attributes):
    return {
        "username": username,
        "email": f"{username}@example.com",
        "attributes": attributes,
        "groups_obj": [],
        "avatar": "",
    }


def mock_directory(*users):
    responses.get(
        SYNC_URL,
        json={"pagination": {"total_pages": 1}, "results": list(users)},
    )


@pytest.mark.django_db
@responses.activate
def test_sync_reports_users_with_missing_attributes_and_continues(caplog):
    mock_directory(
        directory_user("no_attributes", {}),
        directory_user("null_mobile", dict(COMPLETE_ATTRIBUTES, mobile=None)),
        directory_user("complete", COMPLETE_ATTRIBUTES),
    )

    with caplog.at_level(logging.ERROR):
        call_command("sync_bss_users")

    assert (
        "User no_attributes is missing attributes in the directory: "
        "first_name, last_name, mobile." in caplog.text
    )
    assert (
        "User null_mobile is missing attributes in the directory: mobile."
        in caplog.text
    )
    assert not User.objects.filter(
        username__in=["no_attributes", "null_mobile"]
    ).exists()

    # The user after the broken ones must still have been synchronized.
    complete = User.objects.get(username="complete")
    assert complete.first_name == "Test"
    assert complete.phone_number == "+36701234567"


@pytest.mark.django_db
@responses.activate
def test_sync_does_not_demote_a_user_with_missing_attributes():
    user = create_user(username="no_mobile", is_staff=True)
    mock_directory(directory_user("no_mobile", dict(COMPLETE_ATTRIBUTES, mobile="")))

    call_command("sync_bss_users")

    user.refresh_from_db()
    assert user.is_staff
