from datetime import date, datetime, timedelta

import pytest
from django.contrib.auth.models import Group
from django.utils.timezone import localtime, make_aware
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
from social_django.models import UserSocialAuth

from common.models import User
from tests.api.helpers import assert_fields_exist, do_login, get_response, login

pytestmark = pytest.mark.django_db


def assert_list_response_keys(user):
    assert_fields_exist(
        user,
        [
            "avatar_url",
            "email",
            "full_name",
            "id",
            "is_staff",
            "phone_number",
        ],
    )


def assert_retrieve_response_keys(user):
    assert_fields_exist(
        user,
        [
            "ban",
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

    if user["ban"]:
        assert_fields_exist(
            user["ban"],
            [
                "created",
                "creator",
                "reason",
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
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_list_users(api_client, expected, pagination, request, user):
    do_login(api_client, request, user)

    users = baker.make(User, _fill_optional=True, _quantity=5)

    url = reverse("api:v1:admin:users:user-list")
    response = api_client.get(url, {"pagination": pagination})

    assert response.status_code == expected

    if is_success(response.status_code):
        if pagination:
            assert_fields_exist(
                response.data, ["count", "links", "results", "total_pages"]
            )
            assert_fields_exist(response.data["links"], ["next", "previous"])

            assert response.data["count"] == len(users) + 1

        response_data = response.data["results"] if pagination else response.data
        assert len(response_data) == len(users) + 1
        for user in response_data:
            assert_list_response_keys(user)


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
@pytest.mark.parametrize("banned", [True, False])
@pytest.mark.parametrize("has_groups", [True, False])
@pytest.mark.parametrize("has_social_accounts", [True, False])
def test_retrieve_user(
    api_client, banned, expected, has_groups, has_social_accounts, request, user
):
    do_login(api_client, request, user)

    user = baker.make(User, _fill_optional=True)

    if banned:
        ban = baker.make("common.Ban", receiver=user, _fill_optional=True)

    if has_groups:
        groups = baker.make(Group, _quantity=5)
        for group in groups:
            user.groups.add(group)

    if has_social_accounts:
        social_accounts = baker.make(
            UserSocialAuth, user=user, _fill_optional=True, _quantity=2
        )

    url = reverse("api:v1:admin:users:user-detail", kwargs={"pk": user.id})
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)

        if banned:
            ban.refresh_from_db()
            assert response.data["ban"]["created"] == localtime(ban.created).isoformat()
            assert (
                response.data["ban"]["creator"]["avatar_url"] == ban.creator.avatar_url
            )
            assert (
                response.data["ban"]["creator"]["full_name"]
                == ban.creator.get_full_name_eastern_order()
            )
            assert response.data["ban"]["creator"]["id"] == ban.creator.id
            assert response.data["ban"]["reason"] == ban.reason

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
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_own_user(api_client, expected, method, request, user, user_data):
    user = do_login(api_client, request, user)

    url = reverse("api:v1:admin:users:user-detail", kwargs={"pk": user.id})

    response = get_response(api_client, method, url, user_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)

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
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_other_user(api_client, expected, method, request, user, user_data):
    do_login(api_client, request, user)

    user = baker.make(User, _fill_optional=True)

    url = reverse("api:v1:admin:users:user-detail", kwargs={"pk": user.id})

    response = get_response(api_client, method, url, user_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)

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
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["GET", "PATCH", "PUT"])
def test_retrieve_update_user_error(
    api_client, expected, method, not_existing_user_id, request, user, user_data
):
    do_login(api_client, request, user)

    url = reverse("api:v1:admin:users:user-detail", kwargs={"pk": not_existing_user_id})
    response = get_response(api_client, method, url, user_data)

    assert response.status_code == expected


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
@pytest.mark.parametrize("data", ["email", "first_name", "last_name"])
@pytest.mark.parametrize("value", ["", None])
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_user_validation(
    api_client, data, expected, method, request, user, value
):
    user = do_login(api_client, request, user)

    url = reverse("api:v1:admin:users:user-detail", kwargs={"pk": user.id})

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


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_user_email_validation(admin_user, api_client, method, user_data):
    login(api_client, admin_user)

    user_1 = baker.make(User, _fill_optional=True)
    user_2 = baker.make(User, _fill_optional=True)

    url = reverse("api:v1:admin:users:user-detail", kwargs={"pk": user_1.id})

    response = get_response(
        api_client, method, url, user_data | {"email": user_2.email}
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["email"][0] == ErrorDetail(
        "E-mail address already in use.", code="invalid"
    )


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_user_avatar(admin_user, api_client, method):
    login(api_client, admin_user)

    user = baker.make(User, _fill_optional=True)

    avatar_data = {
        "provider": "microsoft-graph",
        "gravatar": "https://example.com/picture2.png",
        "microsoft-graph": "https://example.com/picture1.png",
    }

    user.avatar = avatar_data
    user.save()

    url = reverse("api:v1:admin:users:user-detail", kwargs={"pk": user.id})

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
        ("admin_user", HTTP_201_CREATED),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("data", [{"reason": "Lorem Ipsum"}, None])
def test_create_user_ban(api_client, data, expected, request, user):
    own_user = do_login(api_client, request, user)

    user = baker.make(User, _fill_optional=True)

    url = reverse("api:v1:admin:users:user-ban", kwargs={"pk": user.id})

    response = api_client.post(url, data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_fields_exist(
            response.data,
            [
                "created",
                "creator",
                "reason",
            ],
        )
        assert_fields_exist(
            response.data["creator"],
            [
                "avatar_url",
                "full_name",
                "id",
            ],
        )

        data = data or {}
        assert response.data["reason"] == data.get("reason", "")
        assert response.data["creator"]["avatar_url"] == own_user.avatar_url
        assert (
            response.data["creator"]["full_name"]
            == own_user.get_full_name_eastern_order()
        )
        assert response.data["creator"]["id"] == own_user.id


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_user_ban_validation(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    # Try to ban own user
    url = reverse("api:v1:admin:users:user-ban", kwargs={"pk": user.id})

    response = api_client.post(url, {"reason": "Lorem Ipsum"})

    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["receiver"][0] == ErrorDetail(
            "Users cannot ban themselves.", code="invalid"
        )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_user_ban_error(api_client, expected, request, user):
    do_login(api_client, request, user)

    user = baker.make(User, _fill_optional=True)

    url = reverse("api:v1:admin:users:user-ban", kwargs={"pk": user.id})

    api_client.post(url, {"reason": "Old reason"})

    # Create ban twice
    response = api_client.post(url, {"reason": "New reason"})

    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["receiver"][0] == ErrorDetail(
            "Ban with this Receiver already exists.", code="unique"
        )


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
def test_destroy_user_ban(api_client, expected, request, user):
    own_user = do_login(api_client, request, user)

    user = baker.make(User, _fill_optional=True)

    baker.make("common.Ban", creator=own_user, receiver=user, _fill_optional=True)

    url = reverse("api:v1:admin:users:user-ban", kwargs={"pk": user.id})

    response = api_client.delete(url)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_destroy_user_ban_error(api_client, expected, request, user):
    do_login(api_client, request, user)

    user = baker.make(User, _fill_optional=True)

    url = reverse("api:v1:admin:users:user-ban", kwargs={"pk": user.id})

    response = api_client.delete(url)

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
@pytest.mark.parametrize("was_crew_member", [True, False])
@pytest.mark.parametrize("was_editor", [True, False])
@pytest.mark.parametrize("was_responsible", [True, False])
def test_user_worked_on(
    api_client,
    expected,
    request,
    time_machine,
    user,
    was_crew_member,
    was_editor,
    was_responsible,
):
    time_machine.move_to(datetime(2023, 9, 13))

    do_login(api_client, request, user)

    user = baker.make(User, _fill_optional=True)

    start_datetime = make_aware(
        datetime.combine(date.fromisoformat("2023-09-13"), datetime.min.time())
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

    url = reverse("api:v1:admin:users:user-worked-on", kwargs={"pk": user.id})

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
