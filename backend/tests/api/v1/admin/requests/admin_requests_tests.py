from copy import deepcopy
from datetime import timedelta
from itertools import combinations

import pytest
from django.utils.timezone import localtime
from model_bakery import baker
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    is_success,
)

from common.models import User
from tests.api.helpers import assert_fields_exist, do_login, get_response
from video_requests.models import Comment, Video

pytestmark = pytest.mark.django_db


def assert_list_response_keys(video_request):
    assert_fields_exist(
        video_request,
        [
            "created",
            "crew",
            "deadline",
            "id",
            "start_datetime",
            "status",
            "status_by_admin",
            "responsible",
            "title",
            "video_count",
        ],
    )

    crew = video_request.get("crew")
    if crew:
        for crew_member in crew:
            assert_fields_exist(crew_member, ["avatar_url", "full_name", "id"])

    responsible = video_request.get("responsible")
    if responsible:
        assert_fields_exist(responsible, ["avatar_url", "full_name", "id"])


def assert_retrieve_response_keys(video_request):
    assert_fields_exist(
        video_request,
        [
            "additional_data",
            "comment_count",
            "created",
            "crew",
            "deadline",
            "end_datetime",
            "id",
            "place",
            "requester",
            "requested_by",
            "start_datetime",
            "status",
            "status_by_admin",
            "responsible",
            "title",
            "type",
            "video_count",
            "videos_edited",
        ],
    )

    crew = video_request.get("crew")
    if crew:
        for crew_member in crew:
            assert_fields_exist(crew_member, ["avatar_url", "full_name", "id"])

    requester = video_request.get("requester")
    assert_user_details(requester)

    requested_by = video_request.get("requested_by")
    assert_user_details(requested_by)

    responsible = video_request.get("responsible")
    if responsible:
        assert_user_details(responsible)


def assert_user_details(user):
    assert_fields_exist(
        user, ["avatar_url", "email", "full_name", "id", "is_staff", "phone_number"]
    )


@pytest.fixture
def request_create_data():
    return {
        "end_datetime": localtime() + timedelta(days=1, hours=3),
        "place": "Consectetur adipiscing elit",
        "start_datetime": localtime() + timedelta(days=1),
        "title": "Lorem ipsum dolor sit amet",
        "type": "Ut volutpat auctor neque",
    }


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_list_requests(api_client, expected, pagination, request, user):
    user = do_login(api_client, request, user)

    video_requests = baker.make("video_requests.Request", responsible=user, _quantity=5)
    baker.make("video_requests.CrewMember", _quantity=3, request=video_requests[0])

    url = reverse("api:v1:admin:requests:request-list")
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
        for video_request in response_data:
            assert_list_response_keys(video_request)


@pytest.mark.parametrize(
    "user,expected",
    [
        (
            "admin_user",
            {"PATCH": HTTP_200_OK, "POST": HTTP_201_CREATED, "PUT": HTTP_200_OK},
        ),
        (
            "staff_user",
            {"PATCH": HTTP_200_OK, "POST": HTTP_201_CREATED, "PUT": HTTP_200_OK},
        ),
        (
            "basic_user",
            {
                "PATCH": HTTP_403_FORBIDDEN,
                "POST": HTTP_403_FORBIDDEN,
                "PUT": HTTP_403_FORBIDDEN,
            },
        ),
        (
            "service_account",
            {
                "PATCH": HTTP_403_FORBIDDEN,
                "POST": HTTP_403_FORBIDDEN,
                "PUT": HTTP_403_FORBIDDEN,
            },
        ),
        (
            None,
            {
                "PATCH": HTTP_401_UNAUTHORIZED,
                "POST": HTTP_401_UNAUTHORIZED,
                "PUT": HTTP_401_UNAUTHORIZED,
            },
        ),
    ],
)
@pytest.mark.parametrize(
    "scenario",
    [
        "no-requester",
        "requester-with-data-existing-user",
        "requester-with-data-new-user",
        "requester-with-id",
        "with-comment",
        "with-deadline",
        "with-responsible",
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "POST", "PUT"])
def test_create_update_request(
    api_client, expected, method, request, request_create_data, scenario, user
):
    test_user = baker.make(User, is_staff=True, _fill_optional=["email"])

    user = do_login(api_client, request, user)

    data = deepcopy(request_create_data)

    scenario_data = {
        "no-requester": {},
        "requester-with-data-existing-user": {
            "requester_email": test_user.email,
            "requester_first_name": "Test",
            "requester_last_name": "User",
            "requester_mobile": "+36509999999",
        },
        "requester-with-data-new-user": {
            "requester_email": "test@example.com",
            "requester_first_name": "Test",
            "requester_last_name": "User",
            "requester_mobile": "+36509999999",
        },
        "requester-with-id": {"requester": test_user.id},
        "with-comment": {
            "comment": "Vestibulum dictum nunc lacus, sit amet euismod enim tincidunt a."
            "Proin dignissim tristique turpis vel interdum.",
        },
        "with-deadline": {
            "deadline": (data["end_datetime"] + timedelta(weeks=1)).date()
        },
        "with-responsible": {"responsible": test_user.id},
    }

    if not scenario == "with-comment" or method == "POST":
        data |= scenario_data[scenario]

    if method == "POST":
        url = reverse("api:v1:admin:requests:request-list")
    else:
        video_request = baker.make("video_requests.Request")
        url = reverse(
            "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
        )

    response = get_response(api_client, method, url, data)

    assert response.status_code == expected[method]

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)

        if method == "POST":
            assert response.data["requested_by"]["id"] == user.id

        if scenario == "requester-with-data-existing-user":
            assert User.objects.filter(email__iexact=data["requester_email"]).exists()
            assert response.data["requester"]["id"] == test_user.id
            assert (
                response.data["additional_data"]["requester"]["first_name"]
                == data["requester_first_name"]
            )
            assert (
                response.data["additional_data"]["requester"]["last_name"]
                == data["requester_last_name"]
            )
            assert (
                response.data["additional_data"]["requester"]["phone_number"]
                == data["requester_mobile"]
            )

        elif scenario == "requester-with-data-new-user":
            assert User.objects.filter(email__iexact=data["requester_email"]).exists()

            new_user = User.objects.get(email=data["requester_email"])
            assert new_user.first_name == data["requester_first_name"]
            assert new_user.last_name == data["requester_last_name"]
            assert new_user.phone_number == data["requester_mobile"]
            assert response.data["requester"]["id"] == new_user.id

        elif scenario == "requester-with-id":
            assert response.data["requester"]["id"] == test_user.id

        elif scenario == "with-responsible":
            assert response.data["responsible"]["id"] == test_user.id

        elif method == "POST":
            assert response.data["requester"]["id"] == user.id

        if scenario == "with-comment" and method == "POST":
            assert response.data["comment_count"] == 1
            assert Comment.objects.filter(request=response.data["id"]).exists()

            comment = Comment.objects.get(request=response.data["id"])
            assert comment.author == user
            assert comment.text == data["comment"]

        else:
            assert response.data["comment_count"] == 0

        if scenario == "with-deadline":
            assert response.data["deadline"] == str(data["deadline"])

        else:
            assert response.data["deadline"] == str(
                (data["end_datetime"] + timedelta(weeks=3)).date()
            )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_400_BAD_REQUEST),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "POST", "PUT"])
def test_create_update_request_requester_validation(
    api_client, expected, method, request, request_create_data, user
):
    test_user = baker.make(User, is_staff=True, _fill_optional=["email"])

    do_login(api_client, request, user)

    user_data = [
        {"requester_email": "test@example.com"},
        {"requester_first_name": "Test"},
        {"requester_last_name": "User"},
        {"requester_mobile": "+36509999999"},
    ]

    if method == "POST":
        url = reverse("api:v1:admin:requests:request-list")
    else:
        video_request = baker.make("video_requests.Request")
        url = reverse(
            "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
        )

    for r in range(1, len(user_data) + 1):
        for selected in list(combinations(user_data, r)):
            data = deepcopy(request_create_data)
            for item in selected:
                data |= item
            if r == len(user_data):
                data |= {"requester": test_user.id}
                response = get_response(api_client, method, url, data)
                assert response.status_code == expected
                if response.status_code == HTTP_400_BAD_REQUEST:
                    assert response.data["non_field_errors"][0] == ErrorDetail(
                        string="Either define the requester by its id or its details but not both.",
                        code="invalid",
                    )
            else:
                response = get_response(api_client, method, url, data)
                assert response.status_code == expected
                if response.status_code == HTTP_400_BAD_REQUEST:
                    assert response.data["non_field_errors"][0] == ErrorDetail(
                        string="All requester data fields must be present if one is present.",
                        code="invalid",
                    )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_400_BAD_REQUEST),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "POST", "PUT"])
def test_create_update_request_date_validation(
    api_client, expected, method, request, request_create_data, user
):
    do_login(api_client, request, user)

    if method == "POST":
        url = reverse("api:v1:admin:requests:request-list")
    else:
        video_request = baker.make("video_requests.Request")
        url = reverse(
            "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
        )

    data = deepcopy(request_create_data)
    data["end_datetime"] = data["start_datetime"] - timedelta(hours=2)
    response = get_response(api_client, method, url, data)
    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["end_datetime"][0] == ErrorDetail(
            string="Must be later than the start of the event.", code="invalid"
        )

    data = deepcopy(request_create_data)
    data["deadline"] = data["end_datetime"].date()
    response = get_response(api_client, method, url, data)
    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["deadline"][0] == ErrorDetail(
            string="Must be later than the end of the event.", code="invalid"
        )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_400_BAD_REQUEST),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "POST", "PUT"])
def test_create_update_request_invalid_user(
    api_client,
    expected,
    method,
    not_existing_user_id,
    request,
    request_create_data,
    user,
):
    do_login(api_client, request, user)

    if method == "POST":
        url = reverse("api:v1:admin:requests:request-list")
    else:
        video_request = baker.make("video_requests.Request")
        url = reverse(
            "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
        )

    data = deepcopy(request_create_data)
    data["requester"] = not_existing_user_id
    response = get_response(api_client, method, url, data)
    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["requester"][0].code == "does_not_exist"

    data = deepcopy(request_create_data)
    data["responsible"] = not_existing_user_id
    response = get_response(api_client, method, url, data)
    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["responsible"][0].code == "does_not_exist"


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_request(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_request_status_by_admin(api_client, expected, request, user):
    video_request_1 = baker.make("video_requests.Request", additional_data={})
    video_request_2 = baker.make(
        "video_requests.Request",
        additional_data={
            "status_by_admin": {"status": 5, "admin_id": 1, "admin_name": "Test Admin"}
        },
    )

    do_login(api_client, request, user)

    url_1 = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request_1.id}
    )
    url_2 = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request_2.id}
    )

    response_1 = api_client.get(url_1)
    response_2 = api_client.get(url_2)

    assert response_1.status_code == expected
    assert response_2.status_code == expected

    if is_success(response_1.status_code) and is_success(response_2.status_code):
        assert_retrieve_response_keys(response_1.data)
        assert_retrieve_response_keys(response_2.data)

        assert not response_1.data.get("status_by_admin")
        assert response_2.data.get("status_by_admin")


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_request_videos_edited(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )

    response = api_client.get(url)
    assert response.status_code == expected
    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)
        assert not response.data.get("videos_edited")
        assert response.data.get("video_count") == 0

    video_1 = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.IN_PROGRESS
    )
    response = api_client.get(url)
    assert response.status_code == expected
    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)
        assert not response.data.get("videos_edited")
        assert response.data.get("video_count") == 1

    video_1.status = Video.Statuses.EDITED
    video_1.save()
    response = api_client.get(url)
    assert response.status_code == expected
    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)
        assert response.data.get("videos_edited")
        assert response.data.get("video_count") == 1

    video_2 = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.PENDING
    )
    response = api_client.get(url)
    assert response.status_code == expected
    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)
        assert not response.data.get("videos_edited")
        assert response.data.get("video_count") == 2

    video_2.status = Video.Statuses.DONE
    video_2.save()
    response = api_client.get(url)
    assert response.status_code == expected
    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)
        assert response.data.get("videos_edited")
        assert response.data.get("video_count") == 2


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["GET", "DELETE", "PATCH", "PUT"])
def test_retrieve_update_destroy_request_error(
    api_client, expected, method, not_existing_request_id, request, user
):
    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": not_existing_request_id}
    )
    response = get_response(api_client, method, url, {"title": "Lorem Ipsum"})

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_request_remove_responsible(
    api_client, expected, method, request, request_create_data, user
):
    test_user = baker.make(User, _fill_optional=["email"])
    video_request = baker.make("video_requests.Request", responsible=test_user)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )

    response_before = api_client.get(url)
    response = get_response(
        api_client, method, url, request_create_data | {"responsible": None}
    )

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_user_details(response_before.data["responsible"])
        assert response_before.data["responsible"]["id"] == test_user.id
        assert not response.data["responsible"]


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_400_BAD_REQUEST),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_request_remove_requester_error(
    api_client, expected, method, request, request_create_data, user
):
    test_user = baker.make(User, _fill_optional=["email"])
    video_request = baker.make("video_requests.Request", requester=test_user)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )

    response = get_response(
        api_client, method, url, request_create_data | {"requester": None}
    )

    assert response.status_code == expected

    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["requester"][0] == ErrorDetail(
            string="This field may not be null.", code="null"
        )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_204_NO_CONTENT),
        ("staff_user", HTTP_204_NO_CONTENT),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("scenario", ["requester", "requested_by"])
def test_destroy_own_request(api_client, expected, request, scenario, user):
    user = do_login(api_client, request, user)

    if scenario == "requester":
        video_request = baker.make("video_requests.Request", requester=user)
    else:
        video_request = baker.make("video_requests.Request", requested_by=user)

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )
    response = api_client.delete(url)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_204_NO_CONTENT),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("scenario", ["requester", "requested_by"])
def test_destroy_others_request(api_client, expected, request, scenario, user):
    video_request = baker.make("video_requests.Request")

    user = do_login(api_client, request, user)

    assert video_request.requester != user
    assert video_request.requested_by != user

    url = reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )
    response = api_client.delete(url)

    assert response.status_code == expected
