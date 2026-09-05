from datetime import date, datetime, timedelta

import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.timezone import make_aware
from model_bakery import baker
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_400_BAD_REQUEST, is_success

from common.models import User
from tests.api.helpers import login

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "filters,expected",
    [
        ({"is_admin": False}, 14),
        ({"is_admin": True}, 3),
        ({"is_staff": False}, 9),
        ({"is_staff": True}, 8),
        ({"is_admin": False, "is_staff": False}, 9),
        ({"is_admin": False, "is_staff": True}, 5),
        ({"is_admin": True, "is_staff": False}, 0),
        ({"is_admin": True, "is_staff": True}, 3),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_filter_users(admin_user, api_client, filters, expected, pagination):
    # Create admin users
    admin_users = baker.make(User, is_staff=True, _fill_optional=True, _quantity=2)
    for user in admin_users:
        group = Group.objects.get_or_create(name=settings.ADMIN_GROUP)[0]
        user.groups.add(group)
        user.save()

    # Create staff users
    baker.make(User, is_staff=True, _fill_optional=True, _quantity=5)

    # Create normal users
    baker.make(User, is_staff=False, _fill_optional=True, _quantity=9)

    login(api_client, admin_user)

    url = reverse("api:v1:admin:users:user-list")
    response = api_client.get(url, {"pagination": pagination} | filters)

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == expected


@pytest.mark.parametrize(
    "ordering,expected",
    [
        # Admin user will also be included
        ("email", [1, 2, 6, 3, 5, 4]),
        ("full_name", [2, 6, 4, 3, 5, 1]),
        ("is_staff,full_name", [4, 3, 2, 6, 5, 1]),
        ("userprofile__phone_number", [6, 5, 4, 3, 2, 1]),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_order_users(admin_user, api_client, expected, ordering, pagination):
    users = [
        admin_user,
        baker.make(
            User,
            email="jmillard@example.com",
            first_name="Joselyn",
            last_name="Millard",
            is_staff=True,
            _fill_optional=True,
        ),
        baker.make(
            User,
            email="ksamuel@example.com",
            first_name="Kairo",
            last_name="Samuel",
            is_staff=False,
            _fill_optional=True,
        ),
        baker.make(
            User,
            email="smoores@example.com",
            first_name="Shanelle",
            last_name="Moores",
            is_staff=False,
            _fill_optional=True,
        ),
        baker.make(
            User,
            email="lstrudwick@example.com",
            first_name="Lauren",
            last_name="Strudwick",
            is_staff=True,
            _fill_optional=True,
        ),
        baker.make(
            User,
            email="joseph.millard@example.com",
            first_name="Joseph",
            last_name="Millard",
            is_staff=True,
            _fill_optional=True,
        ),
    ]

    counter = 9
    for user in users:
        user.userprofile.phone_number = f"+3650123456{counter}"
        user.userprofile.save()
        counter = counter - 1

    login(api_client, admin_user)

    url = reverse("api:v1:admin:users:user-list")
    response = api_client.get(url, {"ordering": ordering, "pagination": pagination})

    assert is_success(response.status_code)

    for i, _ in enumerate(users):
        response_data = response.data["results"] if pagination else response.data

        assert response_data[i]["id"] == users[expected[i] - 1].id


@pytest.mark.parametrize("pagination", [True, False])
def test_search_users(admin_user, api_client, pagination):
    users = [
        admin_user,
        baker.make(
            User,
            first_name="Joselyn",
            last_name="Millard",
            _fill_optional=True,
        ),
        baker.make(
            User,
            first_name="Kairo",
            last_name="Samuel",
            _fill_optional=True,
        ),
        baker.make(
            User,
            first_name="Millie",
            last_name="Moores",
            _fill_optional=True,
        ),
        baker.make(
            User,
            first_name="Lauren",
            last_name="Strudwick",
            _fill_optional=True,
        ),
        baker.make(
            User,
            first_name="Joseph",
            last_name="Millard",
            _fill_optional=True,
        ),
    ]

    login(api_client, admin_user)

    url = reverse("api:v1:admin:users:user-list")
    response = api_client.get(url, {"pagination": pagination, "search": "Mil"})

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 3

    assert response_data[0]["id"] == users[1].id
    assert response_data[1]["id"] == users[5].id
    assert response_data[2]["id"] == users[3].id


@pytest.mark.parametrize(
    "filters,expected",
    [
        ({"is_responsible": False}, 4),
        ({"is_responsible": True}, 6),
        ({"is_responsible": False, "start_datetime_after": "1998-08-01"}, 3),
        ({"is_responsible": False, "start_datetime_before": "1998-08-01"}, 1),
        (
            {
                "is_responsible": False,
                "start_datetime_after": "1998-08-01",
                "start_datetime_before": "1998-09-01",
            },
            1,
        ),
        ({"start_datetime_after": "1998-08-01"}, 4),
        ({"start_datetime_before": "1998-08-01"}, 2),
        (
            {
                "start_datetime_after": "1998-08-01",
                "start_datetime_before": "1998-09-01",
            },
            1,
        ),
    ],
)
@pytest.mark.parametrize("use_me_endpoint", [True, False])
def test_filter_worked_on(
    admin_user, api_client, expected, filters, time_machine, use_me_endpoint
):
    time_machine.move_to(datetime(1998, 9, 13))

    login(api_client, admin_user)

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
            "video_requests.Request",
            responsible=admin_user,
            start_datetime=start_datetime - timedelta(days=85),
        ),
        baker.make(
            "video_requests.Request",
            responsible=admin_user,
            start_datetime=start_datetime - timedelta(days=5),
        ),
    ]

    baker.make(
        "video_requests.CrewMember", member=admin_user, request=video_requests[0]
    ),
    baker.make(
        "video_requests.CrewMember", member=admin_user, request=video_requests[1]
    ),
    baker.make(
        "video_requests.CrewMember", member=admin_user, request=video_requests[4]
    ),

    baker.make("video_requests.Video", editor=admin_user, request=video_requests[2]),

    if use_me_endpoint:
        url = reverse("api:v1:me:me-worked-on")
    else:
        url = reverse("api:v1:admin:users:user-worked-on", kwargs={"pk": admin_user.id})

    response = api_client.get(url, filters)

    assert is_success(response.status_code)
    assert len(response.data) == expected


@pytest.mark.parametrize("use_me_endpoint", [True, False])
def test_filter_worked_on_error(admin_user, api_client, use_me_endpoint):
    login(api_client, admin_user)

    if use_me_endpoint:
        url = reverse("api:v1:me:me-worked-on")
    else:
        url = reverse("api:v1:admin:users:user-worked-on", kwargs={"pk": admin_user.id})

    response = api_client.get(url, {"start_datetime_after": "LoremIpsum"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["start_datetime_after"][0] == ErrorDetail(
        string="Invalid filter.",
        code="invalid",
    )

    response = api_client.get(url, {"start_datetime_before": "LoremIpsum"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["start_datetime_before"][0] == ErrorDetail(
        string="Invalid filter.",
        code="invalid",
    )

    response = api_client.get(
        url,
        {"start_datetime_after": "1998-09-01", "start_datetime_before": "1998-08-01"},
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["start_datetime_after"][0] == ErrorDetail(
        string="Must be earlier than start_datetime_before.",
        code="invalid",
    )

    response = api_client.get(url, {"is_responsible": "LoremIpsum"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["is_responsible"][0] == ErrorDetail(
        string="Invalid filter.",
        code="invalid",
    )
