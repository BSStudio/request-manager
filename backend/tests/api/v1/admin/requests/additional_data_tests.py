"""What the admin endpoints accept into ``additional_data``.

The guards themselves are unit tested in tests/unit/api/additional_data_tests.py.
What is left here is the wiring: that the endpoint applies them, merges the result
into what was already stored, and reports the status the new data implies.
"""

from datetime import timedelta

import pytest
from django.utils.timezone import localtime
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from tests.api.helpers import login
from tests.factories import make_user
from video_requests.models import Request, Video

pytestmark = pytest.mark.django_db


@pytest.fixture
def patch_data():
    """A payload touching every field the guards care about."""
    return {
        "additional_data": {
            "status_by_admin": {
                "status": Request.Statuses.ARCHIVED,
                "admin_id": 123,
                "admin_name": "Random Name",
            },
            "accepted": True,
            "failed": True,
            "canceled": True,
            "calendar_id": "123456789abcdefg",
            "requester": {
                "first_name": "Test",
                "last_name": "User",
                "phone_number": "+36701234567",
            },
            "recording": {
                "path": "N:/test_path",
                "copied_to_gdrive": True,
                "removed": False,
            },
        }
    }


@pytest.fixture
def video_request(admin_user):
    return baker.make(
        "video_requests.Request", requester=admin_user, requested_by=admin_user
    )


def request_url(request_id):
    return reverse("api:v1:admin:requests:request-detail", kwargs={"pk": request_id})


def video_url(request_id, video_id):
    return reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": request_id, "pk": video_id},
    )


class TestGuardsAreApplied:
    def test_staff_cannot_write_the_admin_only_fields(
        self, api_client, patch_data, staff_user, video_request
    ):
        login(api_client, staff_user)

        response = api_client.patch(request_url(video_request.id), patch_data)

        assert response.status_code == HTTP_200_OK
        assert response.data["additional_data"] == {
            "recording": {
                "path": "N:/test_path",
                "copied_to_gdrive": True,
                "removed": False,
            }
        }

    def test_an_admin_can_write_all_of_them_except_the_requester_snapshot(
        self, admin_user, api_client, patch_data, video_request
    ):
        login(api_client, admin_user)

        response = api_client.patch(request_url(video_request.id), patch_data)

        assert response.status_code == HTTP_200_OK
        stored = response.data["additional_data"]
        assert set(stored) == {
            "accepted",
            "calendar_id",
            "canceled",
            "failed",
            "recording",
            "status_by_admin",
        }
        assert stored["status_by_admin"]["admin_id"] == admin_user.id
        assert (
            stored["status_by_admin"]["admin_name"]
            == admin_user.get_full_name_eastern_order()
        )


class TestForcedStatusOverSeveralRequests:
    """The stamp only moves when the forced status itself changes."""

    def test_a_second_admin_resending_the_same_status_does_not_take_it_over(
        self, admin_user, api_client, patch_data, video_request
    ):
        login(api_client, admin_user)
        api_client.patch(request_url(video_request.id), patch_data)

        other_admin = make_user(is_admin=True, first_name="NewAdmin")
        login(api_client, other_admin)
        response = api_client.patch(request_url(video_request.id), patch_data)

        stamp = response.data["additional_data"]["status_by_admin"]
        assert stamp["status"] == Request.Statuses.ARCHIVED
        assert stamp["admin_id"] == admin_user.id
        assert stamp["admin_name"] == admin_user.get_full_name_eastern_order()

    def test_changing_the_forced_status_takes_it_over(
        self, admin_user, api_client, patch_data, video_request
    ):
        login(api_client, admin_user)
        api_client.patch(request_url(video_request.id), patch_data)

        other_admin = make_user(is_admin=True, first_name="NewAdmin")
        login(api_client, other_admin)
        response = api_client.patch(
            request_url(video_request.id),
            {
                "additional_data": {
                    "status_by_admin": {
                        "status": Request.Statuses.UPLOADED,
                        "admin_id": 123,
                        "admin_name": "Random Name",
                    }
                }
            },
        )

        stamp = response.data["additional_data"]["status_by_admin"]
        assert stamp["status"] == Request.Statuses.UPLOADED
        assert stamp["admin_id"] == other_admin.id
        assert stamp["admin_name"] == other_admin.get_full_name_eastern_order()

    def test_clearing_the_forced_status_hands_the_request_back_to_the_flow(
        self, admin_user, api_client, patch_data, video_request
    ):
        login(api_client, admin_user)
        response = api_client.patch(request_url(video_request.id), patch_data)
        assert response.data["status"] == Request.Statuses.ARCHIVED

        other_admin = make_user(is_admin=True, first_name="NewAdmin")
        login(api_client, other_admin)
        response = api_client.patch(
            request_url(video_request.id),
            {
                "additional_data": {
                    "status_by_admin": {
                        "status": None,
                        "admin_id": 123,
                        "admin_name": "Random Name",
                    }
                }
            },
        )

        stamp = response.data["additional_data"]["status_by_admin"]
        assert "status" not in stamp
        assert stamp["admin_id"] == other_admin.id
        # patch_data said canceled, which is what the derived flow now sees.
        assert response.data["status"] == Request.Statuses.CANCELED

        video_request.refresh_from_db()
        assert "status" not in video_request.additional_data["status_by_admin"]

    def test_a_forced_status_can_be_set_again_afterwards(
        self, admin_user, api_client, patch_data, video_request
    ):
        login(api_client, admin_user)
        api_client.patch(request_url(video_request.id), patch_data)
        api_client.patch(
            request_url(video_request.id),
            {"additional_data": {"status_by_admin": {"status": None}}},
        )

        response = api_client.patch(
            request_url(video_request.id),
            {
                "additional_data": {
                    "status_by_admin": {
                        "status": Request.Statuses.DONE,
                        "admin_id": 123,
                        "admin_name": "Random Name",
                    }
                }
            },
        )

        stamp = response.data["additional_data"]["status_by_admin"]
        assert stamp["status"] == Request.Statuses.DONE
        assert stamp["admin_id"] == admin_user.id
        assert response.data["status"] == Request.Statuses.DONE


@pytest.mark.parametrize("field", ["accepted", "canceled", "failed"])
class TestUnsettingAField:
    def test_null_removes_a_field_that_was_set(
        self, admin_user, api_client, field, video_request
    ):
        login(api_client, admin_user)

        for value in [True, False]:
            response = api_client.patch(
                request_url(video_request.id), {"additional_data": {field: value}}
            )
            assert response.data["additional_data"][field] is value

            response = api_client.patch(
                request_url(video_request.id), {"additional_data": {field: None}}
            )
            assert field not in response.data["additional_data"]

    def test_null_for_a_field_that_was_never_set_is_a_no_op(
        self, admin_user, api_client, field, video_request
    ):
        login(api_client, admin_user)
        assert field not in video_request.additional_data

        response = api_client.patch(
            request_url(video_request.id), {"additional_data": {field: None}}
        )

        assert response.status_code == HTTP_200_OK
        assert field not in response.data["additional_data"]


class TestPublishingNotificationFlag:
    """Nobody may claim, or un-claim, that the requester has been e-mailed."""

    @pytest.fixture
    def coded_video(self, admin_user, api_client, settings):
        settings.CELERY_TASK_ALWAYS_EAGER = True
        # The request has to *derive* UPLOADED: every video change recalculates
        # it, and a status merely assigned would fall straight back to felkérés.
        start = localtime() - timedelta(days=2)
        video_request = baker.make(
            "video_requests.Request",
            start_datetime=start,
            end_datetime=start + timedelta(hours=2),
            status=Request.Statuses.UPLOADED,
            additional_data={"accepted": True, "recording": {"path": "N:/test"}},
        )
        login(api_client, admin_user)
        response = api_client.post(
            reverse(
                "api:v1:admin:requests:request:video-list",
                kwargs={"request_pk": video_request.id},
            ),
            {
                "title": "New video",
                "editor": admin_user.id,
                "additional_data": {
                    "editing_done": True,
                    "coding": {"website": True},
                },
            },
            format="json",
        )
        assert response.data["status"] == Video.Statuses.CODED
        return video_request, response.data["id"]

    @pytest.mark.parametrize("caller", ["admin_user", "staff_user"])
    def test_it_cannot_be_set_before_the_video_is_published(
        self, api_client, caller, coded_video, request
    ):
        video_request, video_id = coded_video
        login(api_client, request.getfixturevalue(caller))

        response = api_client.patch(
            video_url(video_request.id, video_id),
            {"additional_data": {"publishing": {"email_sent_to_user": False}}},
            format="json",
        )

        assert response.status_code == HTTP_200_OK
        assert (
            "email_sent_to_user" not in response.data["additional_data"]["publishing"]
        )

    @pytest.mark.parametrize("caller", ["admin_user", "staff_user"])
    def test_it_cannot_be_cleared_once_the_e_mail_has_gone_out(
        self, api_client, caller, coded_video, request
    ):
        video_request, video_id = coded_video
        url = video_url(video_request.id, video_id)

        response = api_client.patch(
            url,
            {"additional_data": {"publishing": {"website": "https://example.com"}}},
            format="json",
        )
        assert response.data["status"] == Video.Statuses.PUBLISHED
        # The e-mail goes out from a task, so read the video back for the flag.
        assert api_client.get(url).data["additional_data"]["publishing"][
            "email_sent_to_user"
        ]

        login(api_client, request.getfixturevalue(caller))
        response = api_client.patch(
            url,
            {"additional_data": {"publishing": {"email_sent_to_user": False}}},
            format="json",
        )

        assert response.status_code == HTTP_200_OK
        assert response.data["additional_data"]["publishing"]["email_sent_to_user"]


class TestRequesterChangesAndAdditionalData:
    """Rewriting the requester stores a snapshot without dropping anything else."""

    EXPECTED_SNAPSHOT = {
        "first_name": "Anonymous",
        "last_name": "Tester",
        "phone_number": "+36701234567",
    }

    def requester_data(self, admin_user):
        return {
            "requester_first_name": "Anonymous",
            "requester_last_name": "Tester",
            "requester_email": admin_user.email,
            "requester_mobile": "+36701234567",
        }

    def expected(self, admin_user, patch_data):
        return (
            patch_data["additional_data"]
            | {
                "status_by_admin": {
                    "status": Request.Statuses.ARCHIVED,
                    "admin_id": admin_user.id,
                    "admin_name": admin_user.get_full_name_eastern_order(),
                }
            }
            | {"requester": self.EXPECTED_SNAPSHOT}
        )

    def test_stored_additional_data_survives(
        self, admin_user, api_client, patch_data, video_request
    ):
        login(api_client, admin_user)
        api_client.patch(request_url(video_request.id), patch_data)

        response = api_client.patch(
            request_url(video_request.id), self.requester_data(admin_user)
        )

        assert response.status_code == HTTP_200_OK
        assert response.data["requester"]["id"] == admin_user.id
        assert response.data["requested_by"]["id"] == admin_user.id
        assert response.data["additional_data"] == self.expected(admin_user, patch_data)

    def test_additional_data_sent_in_the_same_body_survives(
        self, admin_user, api_client, patch_data, video_request
    ):
        login(api_client, admin_user)

        response = api_client.patch(
            request_url(video_request.id),
            self.requester_data(admin_user) | patch_data,
        )

        assert response.status_code == HTTP_200_OK
        assert response.data["requester"]["id"] == admin_user.id
        assert response.data["requested_by"]["id"] == admin_user.id
        assert response.data["additional_data"] == self.expected(admin_user, patch_data)


class TestSchemaValidation:
    def test_an_unknown_request_key_is_rejected(
        self, admin_user, api_client, video_request
    ):
        login(api_client, admin_user)

        response = api_client.patch(
            request_url(video_request.id),
            {"additional_data": {"randomKey": "randomValue"}},
        )

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert (
            "Additional properties are not allowed ('randomKey' was unexpected)"
            in response.data["additional_data"][0]
        )

    def test_an_unknown_video_key_is_rejected(
        self, admin_user, api_client, video_request
    ):
        video = baker.make("video_requests.Video", request=video_request)
        login(api_client, admin_user)

        response = api_client.patch(
            video_url(video_request.id, video.id),
            {"additional_data": {"randomKey": "randomValue"}},
        )

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert (
            "Additional properties are not allowed ('randomKey' was unexpected)"
            in response.data["additional_data"][0]
        )
