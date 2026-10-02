"""The ``additional_data`` guards in ``api/v1/admin/requests/helpers.py``.

The derived statuses and the e-mail flow both read this free-form JSON column, so
the API restricts what may be written into it.
"""

import pytest
from model_bakery import baker

from api.v1.admin.requests.helpers import (
    check_and_remove_unauthorized_additional_data,
    is_status_by_admin,
    update_additional_data,
)
from tests.factories import make_user
from video_requests.models import Request

pytestmark = pytest.mark.django_db


class TestUpdateAdditionalData:
    """A recursive merge, because a PATCH only carries the keys that changed."""

    def test_a_new_key_is_added(self):
        assert update_additional_data({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_an_existing_key_is_replaced(self):
        assert update_additional_data({"a": 1}, {"a": 2}) == {"a": 2}

    def test_none_removes_a_key(self):
        assert update_additional_data({"a": 1, "b": 2}, {"a": None}) == {"b": 2}

    def test_none_for_a_key_that_was_never_there_is_a_no_op(self):
        assert update_additional_data({"b": 2}, {"a": None}) == {"b": 2}

    def test_a_nested_dict_is_merged_rather_than_replaced(self):
        original = {"recording": {"path": "N:/old", "removed": False}}

        merged = update_additional_data(original, {"recording": {"path": "N:/new"}})

        assert merged == {"recording": {"path": "N:/new", "removed": False}}

    def test_a_nested_dict_can_arrive_for_a_key_that_did_not_exist(self):
        assert update_additional_data({}, {"recording": {"path": "N:/new"}}) == {
            "recording": {"path": "N:/new"}
        }

    def test_a_nested_key_can_be_removed_on_its_own(self):
        original = {"recording": {"path": "N:/old", "removed": False}}

        merged = update_additional_data(original, {"recording": {"removed": None}})

        assert merged == {"recording": {"path": "N:/old"}}

    def test_a_list_is_replaced_whole(self):
        # The only list in additional_data is "aired", and replacing it is the
        # sole way to delete a date from it.
        original = {"aired": ["2020-01-01", "2020-02-02"]}

        merged = update_additional_data(original, {"aired": ["2020-03-03"]})

        assert merged == {"aired": ["2020-03-03"]}


class TestFieldsNobodyMayWrite:
    @pytest.mark.parametrize("is_admin", [True, False])
    def test_the_requester_snapshot_is_always_dropped(self, is_admin):
        user = make_user(is_admin=is_admin, is_staff=not is_admin)

        cleaned = check_and_remove_unauthorized_additional_data(
            {"requester": {"first_name": "Test"}}, user, None
        )

        assert "requester" not in cleaned

    @pytest.mark.parametrize("is_admin", [True, False])
    def test_the_publishing_notification_flag_is_always_dropped(self, is_admin):
        # Only update_video_status may claim the requester has been e-mailed.
        user = make_user(is_admin=is_admin, is_staff=not is_admin)

        cleaned = check_and_remove_unauthorized_additional_data(
            {
                "publishing": {
                    "website": "https://example.com",
                    "email_sent_to_user": False,
                }
            },
            user,
            None,
        )

        assert cleaned == {"publishing": {"website": "https://example.com"}}


class TestFieldsOnlyAnAdminMayWrite:
    ADMIN_ONLY_FIELDS = [
        "status_by_admin",
        "accepted",
        "canceled",
        "failed",
        "calendar_id",
    ]

    @pytest.fixture
    def payload(self):
        return {
            "status_by_admin": {"status": Request.Statuses.ARCHIVED},
            "accepted": True,
            "canceled": True,
            "failed": True,
            "calendar_id": "123456789abcdefg",
            "recording": {"path": "N:/test_path"},
        }

    def test_staff_lose_all_of_them(self, payload):
        cleaned = check_and_remove_unauthorized_additional_data(
            payload, make_user(is_staff=True), baker.make("video_requests.Request")
        )

        assert cleaned == {"recording": {"path": "N:/test_path"}}

    def test_an_admin_keeps_all_of_them(self, payload):
        admin = make_user(is_admin=True)

        cleaned = check_and_remove_unauthorized_additional_data(
            payload, admin, baker.make("video_requests.Request")
        )

        assert set(cleaned) == set(self.ADMIN_ONLY_FIELDS) | {"recording"}


class TestStatusByAdminStamp:
    """Whoever last changed the forced status owns it, and only they are named."""

    @pytest.fixture
    def admin(self):
        return make_user(is_admin=True, first_name="First")

    @pytest.fixture
    def other_admin(self):
        return make_user(is_admin=True, first_name="Second")

    @staticmethod
    def forced(status):
        return {
            "status_by_admin": {
                "status": status,
                "admin_id": 123,
                "admin_name": "Sent in",
            }
        }

    def test_setting_a_status_stamps_the_admin_who_did_it(self, admin):
        cleaned = check_and_remove_unauthorized_additional_data(
            self.forced(Request.Statuses.ARCHIVED),
            admin,
            baker.make("video_requests.Request"),
        )

        assert cleaned["status_by_admin"] == {
            "status": Request.Statuses.ARCHIVED,
            "admin_id": admin.id,
            "admin_name": admin.get_full_name_eastern_order(),
        }

    def test_resending_the_same_status_does_not_reassign_it(self, admin, other_admin):
        video_request = baker.make(
            "video_requests.Request",
            additional_data={
                "status_by_admin": {
                    "status": Request.Statuses.ARCHIVED,
                    "admin_id": admin.id,
                    "admin_name": admin.get_full_name_eastern_order(),
                }
            },
        )

        cleaned = check_and_remove_unauthorized_additional_data(
            self.forced(Request.Statuses.ARCHIVED), other_admin, video_request
        )

        # Dropped entirely, so the merge leaves the original stamp in place.
        assert "status_by_admin" not in cleaned

    def test_changing_the_status_reassigns_it(self, admin, other_admin):
        video_request = baker.make(
            "video_requests.Request",
            additional_data={
                "status_by_admin": {
                    "status": Request.Statuses.ARCHIVED,
                    "admin_id": admin.id,
                    "admin_name": admin.get_full_name_eastern_order(),
                }
            },
        )

        cleaned = check_and_remove_unauthorized_additional_data(
            self.forced(Request.Statuses.UPLOADED), other_admin, video_request
        )

        assert cleaned["status_by_admin"] == {
            "status": Request.Statuses.UPLOADED,
            "admin_id": other_admin.id,
            "admin_name": other_admin.get_full_name_eastern_order(),
        }

    def test_clearing_the_status_reassigns_it_too(self, admin, other_admin):
        video_request = baker.make(
            "video_requests.Request",
            additional_data={
                "status_by_admin": {
                    "status": Request.Statuses.ARCHIVED,
                    "admin_id": admin.id,
                    "admin_name": admin.get_full_name_eastern_order(),
                }
            },
        )

        cleaned = check_and_remove_unauthorized_additional_data(
            self.forced(None), other_admin, video_request
        )

        assert cleaned["status_by_admin"]["admin_id"] == other_admin.id
        assert cleaned["status_by_admin"]["status"] is None

    def test_clearing_a_status_that_was_never_set_is_dropped(self, admin):
        cleaned = check_and_remove_unauthorized_additional_data(
            self.forced(None), admin, baker.make("video_requests.Request")
        )

        assert "status_by_admin" not in cleaned

    @pytest.mark.xfail(
        raises=AttributeError,
        strict=True,
        reason=(
            "Bug: on create the serializer passes original_data=None, and the "
            "second half of the condition dereferences it unconditionally. "
            "POST /api/v1/admin/requests with additional_data.status_by_admin "
            "answers 500."
        ),
    )
    def test_a_forced_status_may_be_set_while_creating(self, admin):
        cleaned = check_and_remove_unauthorized_additional_data(
            self.forced(Request.Statuses.ARCHIVED), admin, None
        )

        assert cleaned["status_by_admin"]["admin_id"] == admin.id


class TestIsStatusByAdmin:
    def test_true_when_a_status_is_forced(self):
        video_request = baker.make(
            "video_requests.Request",
            additional_data={"status_by_admin": {"status": Request.Statuses.DONE}},
        )

        assert is_status_by_admin(video_request) is True

    @pytest.mark.parametrize(
        "additional_data",
        [
            {},
            {"status_by_admin": {}},
            {"status_by_admin": {"status": None}},
        ],
        ids=["nothing_forced", "no_status_key", "status_cleared"],
    )
    def test_false_otherwise(self, additional_data):
        video_request = baker.make(
            "video_requests.Request", additional_data=additional_data
        )

        assert is_status_by_admin(video_request) is False
