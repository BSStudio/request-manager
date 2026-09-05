from datetime import date, datetime, timedelta

import pytest
from django.contrib.auth.models import Group
from django.utils.timezone import make_aware
from model_bakery import baker
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    is_success,
)
from social_django.models import UserSocialAuth

from common.models import User
from tests.api.helpers import assert_fields_exist, do_login, get_response

pytestmark = pytest.mark.django_db


def assert_response_keys(user):
    assert_fields_exist(
        user,
        [
            "email",
            "first_name",
            "groups",
            "id",
            "last_name",
            "profile",
            "role",
            "social_accounts",
            "username",
        ],
    )

    assert_fields_exist(
        user["profile"],
        [
            "avatar",
            "avatar_url",
            "phone_number",
        ],
    )

    if user["social_accounts"]:
        for social_account in user["social_accounts"]:
            assert_fields_exist(social_account, ["provider", "uid"])


@pytest.fixture
def user_data():
    return {
        "email": "changed@example.com",
        "first_name": "Changed",
        "last_name": "Test",
        "profile": {"phone_number": "+36701111111"},
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
@pytest.mark.parametrize("has_groups", [True, False])
@pytest.mark.parametrize("has_social_accounts", [True, False])
def test_retrieve_me(
    api_client, expected, has_groups, has_social_accounts, request, user
):
    user = do_login(api_client, request, user)

    if has_groups:
        groups = baker.make(Group, _quantity=5)
        for group in groups:
            user.groups.add(group)

    if has_social_accounts:
        social_accounts = baker.make(
            UserSocialAuth, user=user, _fill_optional=True, _quantity=2
        )

    url = reverse("api:v1:me:me-detail")
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)

        if has_groups:
            for group in groups:
                assert group.name in response.data["groups"]

        if has_social_accounts:
            for social_account in social_accounts:
                assert any(
                    response_social_account["provider"] == social_account.provider
                    for response_social_account in response.data["social_accounts"]
                )
                assert any(
                    response_social_account["uid"] == social_account.uid
                    for response_social_account in response.data["social_accounts"]
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
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_me(api_client, expected, method, request, user, user_data):
    do_login(api_client, request, user)

    url = reverse("api:v1:me:me-detail")

    response = get_response(api_client, method, url, user_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)

        assert response.data["email"] == user_data["email"]
        assert response.data["first_name"] == user_data["first_name"]
        assert response.data["last_name"] == user_data["last_name"]
        assert (
            response.data["profile"]["phone_number"]
            == user_data["profile"]["phone_number"]
        )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_400_BAD_REQUEST),
        ("basic_user", HTTP_400_BAD_REQUEST),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("data", ["email", "first_name", "last_name"])
@pytest.mark.parametrize("value", ["", None])
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_me_validation(api_client, data, expected, method, request, user, value):
    do_login(api_client, request, user)

    url = reverse("api:v1:me:me-detail")

    response = get_response(api_client, method, url, {data: value})

    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        if value is None:
            assert response.data[data][0] == ErrorDetail(
                "This field may not be null.", code="null"
            )
        else:
            assert response.data[data][0] == ErrorDetail(
                "This field may not be blank.", code="blank"
            )


@pytest.mark.parametrize(
    "user",
    ["admin_user", "staff_user", "basic_user"],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_user_email_validation(api_client, method, request, user, user_data):
    do_login(api_client, request, user)

    user_2 = baker.make(User, _fill_optional=True)

    url = reverse("api:v1:me:me-detail")

    response = get_response(
        api_client, method, url, user_data | {"email": user_2.email}
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["email"][0] == ErrorDetail(
        "E-mail address already in use.", code="invalid"
    )


@pytest.mark.parametrize(
    "user",
    ["admin_user", "staff_user", "basic_user"],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_me_avatar(api_client, method, user, request):
    user = do_login(api_client, request, user)

    avatar_data = {
        "provider": "microsoft-graph",
        "gravatar": "https://example.com/picture2.png",
        "microsoft-graph": "https://example.com/picture1.png",
    }

    user.userprofile.avatar = avatar_data
    user.userprofile.save()

    url = reverse("api:v1:me:me-detail")

    # Check with initial settings
    response = api_client.get(url)

    assert response.status_code == HTTP_200_OK

    assert response.data["profile"]["avatar"]["provider"] == "microsoft-graph"
    assert response.data["profile"]["avatar_url"] == avatar_data["microsoft-graph"]

    # Modify avatar provider
    response = get_response(
        api_client, method, url, {"profile": {"avatar_provider": "gravatar"}}
    )

    assert response.status_code == HTTP_200_OK

    assert response.data["profile"]["avatar"]["provider"] == "gravatar"
    assert response.data["profile"]["avatar_url"] == avatar_data["gravatar"]

    # Error: Avatar does not exist for this provider
    response = get_response(
        api_client, method, url, {"profile": {"avatar_provider": "google-oauth2"}}
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["avatar"][0] == ErrorDetail(
        "Avatar does not exist for this provider.", code="invalid"
    )

    # Error: Provider is not supported
    response = get_response(
        api_client, method, url, {"profile": {"avatar_provider": "random-provider"}}
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["profile"]["avatar_provider"][0] == ErrorDetail(
        '"random-provider" is not a valid choice.', code="invalid_choice"
    )


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
@pytest.mark.parametrize("was_crew_member", [True, False])
@pytest.mark.parametrize("was_editor", [True, False])
@pytest.mark.parametrize("was_responsible", [True, False])
def test_me_worked_on(
    api_client,
    expected,
    request,
    time_machine,
    user,
    was_crew_member,
    was_editor,
    was_responsible,
):
    time_machine.move_to(datetime(1998, 9, 13))

    user = do_login(api_client, request, user)

    start_datetime = make_aware(
        datetime.combine(date.fromisoformat("1998-09-13"), datetime.min.time())
    )

    video_requests = [
        baker.make(
            "video_requests.Request",
            start_datetime=start_datetime - timedelta(weeks=10),
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(weeks=3)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(weeks=1)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=17)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(weeks=6)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=38)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=99)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=45)
        ),
    ]

    should_find = []

    if was_crew_member:
        crew_members = [
            baker.make(
                "video_requests.CrewMember", member=user, request=video_requests[0]
            ),
            baker.make(
                "video_requests.CrewMember", member=user, request=video_requests[0]
            ),
            baker.make(
                "video_requests.CrewMember", member=user, request=video_requests[1]
            ),
            baker.make(
                "video_requests.CrewMember", member=user, request=video_requests[1]
            ),
            baker.make(
                "video_requests.CrewMember", member=user, request=video_requests[1]
            ),
            baker.make(
                "video_requests.CrewMember", member=user, request=video_requests[4]
            ),
            baker.make(
                "video_requests.CrewMember", member=user, request=video_requests[7]
            ),
        ]
        for crew_member in crew_members:
            should_find.append(
                {"id": crew_member.request.id, "position": crew_member.position}
            )

    if was_editor:
        videos = [
            baker.make("video_requests.Video", editor=user, request=video_requests[2]),
            baker.make("video_requests.Video", editor=user, request=video_requests[2]),
            baker.make("video_requests.Video", editor=user, request=video_requests[4]),
            baker.make("video_requests.Video", editor=user, request=video_requests[5]),
            baker.make("video_requests.Video", editor=user, request=video_requests[7]),
        ]
        for video in videos:
            should_find.append({"id": video.request.id, "position": "Editor"})

    if was_responsible:
        video_requests += [
            baker.make(
                "video_requests.Request",
                responsible=user,
                start_datetime=start_datetime - timedelta(days=85),
            ),
            baker.make(
                "video_requests.Request",
                responsible=user,
                start_datetime=start_datetime - timedelta(weeks=7),
            ),
        ]
        should_find.append({"id": video_requests[8].id, "position": "Responsible"})
        should_find.append({"id": video_requests[9].id, "position": "Responsible"})
        video_requests[1].responsible = user
        video_requests[1].save()
        should_find.append({"id": video_requests[1].id, "position": "Responsible"})
        video_requests[7].responsible = user
        video_requests[7].save()
        should_find.append({"id": video_requests[7].id, "position": "Responsible"})

    url = reverse("api:v1:me:me-worked-on")

    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert len(response.data) == len(should_find)
        for video_request in response.data:
            assert_fields_exist(
                video_request,
                [
                    "id",
                    "position",
                    "start_datetime",
                    "title",
                ],
            )
            assert any(
                expected_find["id"] == video_request["id"]
                and expected_find["position"] == video_request["position"]
                for expected_find in should_find
            )
