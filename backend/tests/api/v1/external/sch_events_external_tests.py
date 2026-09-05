import json
from datetime import timedelta

import pytest
import responses
from django.utils.timezone import localtime
from django_celery_results.models import TaskResult
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    is_success,
)

from common.models import User
from tests.api.helpers import assert_fields_exist, do_login, login
from video_requests.models import Comment, Request

pytestmark = pytest.mark.django_db


def assert_comment_response_keys(comment):
    assert_fields_exist(comment, ["author", "created", "id", "text"])

    author = comment.get("author")
    assert_fields_exist(author, ["avatar_url", "full_name", "id"])


def assert_request_response_keys(video_request):
    assert_fields_exist(
        video_request,
        [
            "created",
            "end_datetime",
            "id",
            "place",
            "requester",
            "requested_by",
            "responsible",
            "start_datetime",
            "status",
            "title",
            "type",
        ],
    )

    requester = video_request.get("requester")
    assert_user_details(requester)

    requested_by = video_request.get("requested_by")
    assert_requested_by_details(requested_by)

    responsible = video_request.get("responsible")
    if responsible:
        assert_user_details(responsible)


def assert_user_details(user):
    assert_fields_exist(
        user, ["avatar_url", "email", "full_name", "id", "is_staff", "phone_number"]
    )


def assert_requested_by_details(user):
    assert_fields_exist(user, ["avatar_url", "full_name", "id"])


@pytest.fixture
def request_create_data():
    return {
        "callback_url": "https://example.com/api/callback/123",
        "end_datetime": localtime() + timedelta(days=1, hours=3),
        "place": "Consectetur adipiscing elit",
        "start_datetime": localtime() + timedelta(days=1),
        "title": "Lorem ipsum dolor sit amet",
        "type": "Ut volutpat auctor neque",
    }


@pytest.fixture
def requester_data():
    return {
        "requester_email": "test@example.com",
        "requester_first_name": "Test",
        "requester_last_name": "User",
        "requester_mobile": "+36509999999",
    }


@pytest.fixture
def comment_data():
    return {"text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_403_FORBIDDEN),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_201_CREATED),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("new_user", [True, False])
@pytest.mark.parametrize("with_comment", [True, False])
def test_create_request(
    api_client,
    expected,
    new_user,
    request,
    request_create_data,
    requester_data,
    user,
    with_comment,
):
    requested_by = do_login(api_client, request, user)
    user = baker.make(User, _fill_optional=["email"])

    if not new_user:
        requester_data |= {"requester_email": user.email}
    else:  # Verify user with this e-mail address doesn't exist
        assert not User.objects.filter(email=requester_data["requester_email"]).exists()

    data = request_create_data | requester_data

    if with_comment:
        data |= {"comment": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}

    url = reverse("api:v1:external:sch-events:requests:request-create")
    response = api_client.post(url, data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_request_response_keys(response.data)
        request = Request.objects.get(pk=response.data["id"])
        requester = User.objects.filter(email=requester_data["requester_email"]).first()
        assert requester
        if not new_user:
            assert requester == user
            assert (
                request.additional_data["requester"]["first_name"]
                == requester_data["requester_first_name"]
            )
            assert (
                request.additional_data["requester"]["last_name"]
                == requester_data["requester_last_name"]
            )
            assert (
                request.additional_data["requester"]["phone_number"]
                == requester_data["requester_mobile"]
            )
        assert response.data["requester"]["id"] == requester.id
        assert response.data["requested_by"]["id"] == requested_by.id
        assert (
            request.additional_data["external"]["sch_events_callback_url"]
            == request_create_data["callback_url"]
        )

        if with_comment:
            comment = Comment.objects.filter(request=request).first()
            assert comment
            assert comment.text == data["comment"]
            assert comment.author == requester


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_403_FORBIDDEN),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_200_OK),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_request(
    api_client,
    expected,
    request,
    user,
):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requested_by=user)

    url = reverse(
        "api:v1:external:sch-events:requests:request-detail",
        kwargs={"pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_request_response_keys(response.data)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_403_FORBIDDEN),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_404_NOT_FOUND),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_request_errors(
    api_client,
    expected,
    not_existing_request_id,
    request,
    user,
):
    user = do_login(api_client, request, user)

    video_request_1 = baker.make("video_requests.Request", requester=user)
    video_request_2 = baker.make("video_requests.Request")

    url = reverse(
        "api:v1:external:sch-events:requests:request-detail",
        kwargs={"pk": video_request_1.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    url = reverse(
        "api:v1:external:sch-events:requests:request-detail",
        kwargs={"pk": video_request_2.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    url = reverse(
        "api:v1:external:sch-events:requests:request-detail",
        kwargs={"pk": not_existing_request_id},
    )
    response = api_client.get(url)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_403_FORBIDDEN),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_201_CREATED),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_comment(
    api_client,
    comment_data,
    expected,
    request,
    user,
):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requested_by=user)

    url = reverse(
        "api:v1:external:sch-events:requests:request-comment-create",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.post(url, comment_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_comment_response_keys(response.data)
        assert response.data["text"] == comment_data["text"]
        assert response.data["author"]["id"] == user.id


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_403_FORBIDDEN),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_404_NOT_FOUND),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_comment_errors(
    api_client,
    comment_data,
    expected,
    not_existing_request_id,
    request,
    user,
):
    user = do_login(api_client, request, user)

    video_request_1 = baker.make("video_requests.Request", requester=user)
    video_request_2 = baker.make("video_requests.Request")

    url = reverse(
        "api:v1:external:sch-events:requests:request-comment-create",
        kwargs={"request_pk": video_request_1.id},
    )
    response = api_client.post(url, comment_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:external:sch-events:requests:request-comment-create",
        kwargs={"request_pk": video_request_2.id},
    )
    response = api_client.post(url, comment_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:external:sch-events:requests:request-comment-create",
        kwargs={"request_pk": not_existing_request_id},
    )
    response = api_client.post(url, comment_data)

    assert response.status_code == expected


@responses.activate
def test_external_callback_on_status_changes(admin_user, api_client, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    login(api_client, admin_user)

    external_url_1 = "https://example.com/api/callback/123"
    external_url_2 = "https://example.com/api/callback/456"

    video_request_1 = baker.make(
        "video_requests.Request",
        additional_data={"external": {"sch_events_callback_url": external_url_1}},
    )

    video_request_2 = baker.make(
        "video_requests.Request",
        additional_data={"external": {"sch_events_callback_url": external_url_2}},
    )

    responses.head(external_url_1)
    responses.head(external_url_2)
    response1 = responses.post(external_url_1, json={"status": "ok"})
    response2 = responses.post(external_url_2, json={"status": "ok"})

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request_1.id}
    )

    # Request changed from Requested to Accepted
    api_client.patch(url, {"additional_data": {"accepted": True}})
    assert response1.call_count == 1
    assert json.loads(response1.calls[0].request.body) == {"accept": True}

    # Request changed from Accepted to Denied
    api_client.patch(url, {"additional_data": {"accepted": False}})
    assert response1.call_count == 2
    assert json.loads(response1.calls[1].request.body) == {"accept": False}

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request_2.id}
    )

    # Request changed from Requested to Denied
    api_client.patch(url, {"additional_data": {"accepted": False}})
    assert response2.call_count == 1
    assert json.loads(response2.calls[0].request.body) == {"accept": False}

    # Request changed from Denied to Accepted
    api_client.patch(url, {"additional_data": {"accepted": True}})
    assert response2.call_count == 2
    assert json.loads(response2.calls[1].request.body) == {"accept": True}


@responses.activate
@pytest.mark.parametrize("accepted", [True, False])
def test_external_callback_on_status_changes_redirect_and_result(
    accepted, admin_user, api_client, settings
):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_STORE_EAGER_RESULT = True

    callback_url = "https://example.com/api/callback/123"
    redirected_callback_url = "https://redirected.example.com/api/callback/123"

    mock_head_redirect = responses.head(
        callback_url, status=301, headers={"Location": redirected_callback_url}
    )
    mock_head = responses.head(redirected_callback_url, status=504)
    mock_post = responses.post(
        redirected_callback_url, status=200, json={"status": "ok"}
    )

    video_request = baker.make(
        "video_requests.Request",
        additional_data={
            "external": {
                "sch_events_callback_url": "https://example.com/api/callback/123"
            }
        },
    )

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )
    api_client.patch(url, {"additional_data": {"accepted": accepted}})

    assert mock_head_redirect.call_count == 1
    assert mock_head.call_count == 1
    assert mock_post.call_count == 1
    assert json.loads(mock_post.calls[0].request.body) == {"accept": accepted}
    assert (
        mock_post.calls[0].request.headers.items()
        >= {
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.SCH_EVENTS_TOKEN}",
            "Content-Type": "application/json",
        }.items()
    )

    assert json.loads(
        TaskResult.objects.get(
            task_args__exact=f"[{video_request.id}]",
            task_name__exact="video_requests.utilities.notify_sch_event_management_system",
        ).result
    ) == {"status": "ok"}


@responses.activate
def test_external_callback_retry(admin_user, api_client, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_STORE_EAGER_RESULT = True

    callback_url = "https://example.com/api/callback/123"

    responses.head(callback_url)
    mock_post = responses.post(callback_url, status=500)

    video_request = baker.make(
        "video_requests.Request",
        additional_data={"external": {"sch_events_callback_url": callback_url}},
    )

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )
    api_client.patch(url, {"additional_data": {"accepted": True}})

    assert mock_post.call_count == 11

    assert (
        TaskResult.objects.get(
            task_args__exact=f"[{video_request.id}]",
            task_name__exact="video_requests.utilities.notify_sch_event_management_system",
        ).status
        == "FAILURE"
    )
