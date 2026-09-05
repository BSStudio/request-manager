from datetime import date, datetime, timedelta
from itertools import combinations
from uuid import uuid4

import pytest
from django.utils.timezone import localtime, make_aware
from model_bakery import baker
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    is_success,
)

from common.models import User, get_anonymous_user
from tests.api.helpers import assert_fields_exist, do_login, login
from video_requests.models import Comment, Request

pytestmark = pytest.mark.django_db


def assert_list_response_keys(video_request):
    assert_fields_exist(
        video_request,
        [
            "created",
            "id",
            "start_datetime",
            "status",
            "title",
        ],
    )


def assert_retrieve_response_keys(video_request):
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


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_200_OK),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_list_requests(api_client, expected, pagination, request, user):
    user = do_login(api_client, request, user)

    video_requests = baker.make("video_requests.Request", requester=user, _quantity=5)
    video_requests_should_not_find = baker.make("video_requests.Request", _quantity=5)

    url = reverse("api:v1:requests:request-list")
    response = api_client.get(url, {"pagination": pagination})

    assert response.status_code == expected

    if is_success(response.status_code):
        if pagination:
            assert_fields_exist(
                response.data, ["count", "links", "results", "total_pages"]
            )
            assert_fields_exist(response.data["links"], ["next", "previous"])

            assert response.data["count"] == len(video_requests)

        response_data = response.data["results"] if pagination else response.data
        assert len(response_data) == len(video_requests)
        for request in response_data:
            assert_list_response_keys(request)
            assert not any(
                request["id"] == should_not_find_request.id
                for should_not_find_request in video_requests_should_not_find
            )


@pytest.mark.parametrize("user", ["admin_user", "staff_user", "basic_user"])
def test_create_request_logged_in(api_client, request, request_create_data, user):
    user = do_login(api_client, request, user)

    url = reverse("api:v1:requests:request-list")
    response = api_client.get(url, {"pagination": True})
    assert response.data["count"] == 0

    url = reverse("api:v1:requests:request-list")
    response = api_client.post(url, request_create_data)

    assert response.status_code == HTTP_201_CREATED
    assert_retrieve_response_keys(response.data)
    assert response.data["requester"]["id"] == user.id
    assert response.data["requested_by"]["id"] == user.id

    url = reverse("api:v1:requests:request-list")
    response = api_client.get(url, {"pagination": True})
    assert response.data["count"] == 1


def test_create_request_service_account(
    api_client, request_create_data, service_account
):
    login(api_client, service_account)

    url = reverse("api:v1:requests:request-list")
    response = api_client.post(url, request_create_data)

    assert response.status_code == HTTP_201_CREATED
    assert_retrieve_response_keys(response.data)
    assert response.data["requester"]["id"] == service_account.id
    assert response.data["requested_by"]["id"] == service_account.id


@pytest.mark.parametrize(
    "new_user",
    [True, False],
)
@pytest.mark.parametrize(
    "captcha_pass",
    [True, False],
)
def test_create_request_anonymous(
    api_client, captcha_pass, new_user, request_create_data, requester_data, settings
):
    settings.TURNSTILE_TESTING_PASS = captcha_pass
    user = baker.make(User, _fill_optional=["email"])

    if not new_user:
        requester_data |= {"requester_email": user.email}
    else:  # Verify user with this e-mail address doesn't exist
        assert not User.objects.filter(email=requester_data["requester_email"]).exists()

    url = reverse("api:v1:requests:request-list")
    response = api_client.post(
        url,
        request_create_data
        | requester_data
        | {"captcha": "randomCaptchaResponseToken"},
    )

    if captcha_pass:
        assert response.status_code == HTTP_201_CREATED
        assert_retrieve_response_keys(response.data)
        requester = User.objects.filter(email=requester_data["requester_email"]).first()
        assert requester
        if not new_user:
            assert requester == user
            request = Request.objects.get(pk=response.data["id"])
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
        assert response.data["requested_by"]["id"] == get_anonymous_user().id

    else:
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.data["captcha"][0] == ErrorDetail(
            string="Error verifying captcha, please try again.",
            code="captcha_invalid",
        )


@pytest.mark.parametrize(
    "user", ["admin_user", "staff_user", "basic_user", "service_account", None]
)
def test_create_request_with_comment(
    api_client, request, request_create_data, requester_data, settings, user
):
    settings.TURNSTILE_TESTING_PASS = True
    if user is None:
        data = (
            request_create_data
            | requester_data
            | {"captcha": "randomCaptchaResponseToken"}
        )
    else:
        data = request_create_data

    do_login(api_client, request, user)

    data |= {"comment": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}

    url = reverse("api:v1:requests:request-list")
    response = api_client.post(url, data)

    assert response.status_code == HTTP_201_CREATED
    assert_retrieve_response_keys(response.data)

    comment = Comment.objects.filter(request__pk=response.data["id"]).first()
    assert comment
    assert comment.text == data["comment"]
    assert comment.author.id == response.data["requester"]["id"]


@pytest.mark.parametrize(
    "user", ["admin_user", "staff_user", "basic_user", "service_account", None]
)
def test_create_request_date_validation(
    api_client, request, request_create_data, requester_data, settings, user
):
    settings.TURNSTILE_TESTING_PASS = True
    if user is None:
        data = (
            request_create_data
            | requester_data
            | {"captcha": "randomCaptchaResponseToken"}
        )
    else:
        data = request_create_data

    do_login(api_client, request, user)

    data |= {"start_datetime": localtime() - timedelta(days=10)}

    url = reverse("api:v1:requests:request-list")
    response = api_client.post(url, data)

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["start_datetime"][0] == ErrorDetail(
        string="Must be later than current time.", code="invalid"
    )

    data |= {
        "end_datetime": localtime() - timedelta(days=25),
        "start_datetime": localtime() + timedelta(days=10),
    }

    url = reverse("api:v1:requests:request-list")
    response = api_client.post(url, data)

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["end_datetime"][0] == ErrorDetail(
        string="Must be later than the start of the event.", code="invalid"
    )


def test_create_request_user_info_validation(api_client, request_create_data):
    url = reverse("api:v1:requests:request-list")

    user_data = [
        {"email": "test@example.com"},
        {"first_name": "Test"},
        {"last_name": "User"},
        {"phone_number": "+36509999999"},
    ]

    for r in range(1, len(user_data) + 1):
        for selected in list(combinations(user_data, r)):
            data = {}
            for item in selected:
                data |= item

            if r == len(user_data):
                data = {}  # All data should work change it to none instead

            user = User.objects.create_user(
                email=data.get("email", ""),
                first_name=data.get("first_name", ""),
                is_staff=False,
                last_name=data.get("last_name", ""),
                password="password",
                username=uuid4(),
            )

            user.userprofile.phone_number = data.get("phone_number", "")
            user.userprofile.save()

            login(api_client, user)
            response = api_client.post(url, request_create_data)

            assert response.status_code == HTTP_400_BAD_REQUEST
            assert response.data["non_field_errors"][0] == ErrorDetail(
                string="Please fill all data in your profile before sending a request.",
                code="invalid",
            )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_200_OK),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_request(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)

    url = reverse(
        "api:v1:requests:request-detail",
        kwargs={"pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_404_NOT_FOUND),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_request_error(
    api_client, expected, not_existing_request_id, request, user
):
    do_login(api_client, request, user)

    # Requester is not the logged-in user
    video_request = baker.make("video_requests.Request")

    url = reverse(
        "api:v1:requests:request-detail",
        kwargs={"pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    url = reverse(
        "api:v1:requests:request-detail",
        kwargs={"pk": not_existing_request_id},
    )
    response = api_client.get(url)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "ordering,expected",
    [
        ("created", [2, 4, 3, 1]),
        ("start_datetime", [4, 2, 3, 1]),
        ("status", [3, 4, 2, 1]),
        ("title", [2, 4, 1, 3]),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_order_requests(
    api_client, basic_user, expected, ordering, pagination, time_machine
):
    requests = []

    start_date = make_aware(
        datetime.combine(date.fromisoformat("2023-05-30"), datetime.min.time())
    )

    time_machine.move_to(datetime(2019, 6, 4))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date,
            requester=basic_user,
            start_datetime=start_date - timedelta(days=4),
            status=Request.Statuses.CANCELED,
            title="CCCC",
        )
    )

    time_machine.move_to(datetime(1990, 8, 7))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date,
            requester=basic_user,
            start_datetime=start_date - timedelta(days=10),
            status=Request.Statuses.DONE,
            title="AAAA",
        )
    )

    time_machine.move_to(datetime(2009, 8, 22))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date,
            requester=basic_user,
            start_datetime=start_date - timedelta(days=8),
            status=Request.Statuses.ACCEPTED,
            title="DDDD",
        )
    )

    time_machine.move_to(datetime(1995, 10, 26))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date,
            requester=basic_user,
            start_datetime=start_date - timedelta(days=15),
            status=Request.Statuses.UPLOADED,
            title="BBBB",
        )
    )

    login(api_client, basic_user)

    url = reverse("api:v1:requests:request-list")
    response = api_client.get(url, {"ordering": ordering, "pagination": pagination})

    assert is_success(response.status_code)

    for i, _ in enumerate(requests):
        response_data = response.data["results"] if pagination else response.data

        assert response_data[i]["id"] == requests[expected[i] - 1].id


@pytest.mark.parametrize("pagination", [True, False])
def test_search_requests(api_client, basic_user, pagination):
    requests = [
        baker.make(
            "video_requests.Request", requester=basic_user, title="AAAA BBBB CCCC"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBBB AAAA CCCC"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="CCCC BBBB AAAA"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBCC CCAA AABB"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBBB CCCC BBBB"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBBB BBBB BBBB"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="CCCC CCCC CCCC"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="CCCC BBBB CCCC"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBAA CCAA AACC"
        ),
    ]

    baker.make("video_requests.Video", request=requests[6], title="AAAA BBBB"),
    baker.make("video_requests.Video", request=requests[7], title="CCCC AAAA"),

    login(api_client, basic_user)

    url = reverse("api:v1:requests:request-list")
    response = api_client.get(url, {"pagination": pagination, "search": "AAAA"})

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 5

    assert response_data[0]["id"] == requests[0].id
    assert response_data[1]["id"] == requests[1].id
    assert response_data[2]["id"] == requests[2].id
    assert response_data[3]["id"] == requests[6].id
    assert response_data[4]["id"] == requests[7].id
