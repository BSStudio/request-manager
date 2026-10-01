import pytest
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from common.models import User
from tests.api.helpers import login

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "ordering,expected",
    [
        # Add position as secondary ordering field to make tests consistent.
        ("member__first_name,position", [1, 5, 2, 6, 3, 4]),
        ("member__last_name,position", [5, 3, 4, 6, 1, 2]),
        ("member__last_name,member__first_name,position", [5, 6, 3, 4, 1, 2]),
        ("position", [1, 5, 2, 3, 4, 6]),
    ],
)
def test_order_crew(admin_user, api_client, expected, ordering):
    video_request = baker.make("video_requests.Request")

    test_crew_member_1 = baker.make(User, first_name="AAAA", last_name="CCCC")
    test_crew_member_2 = baker.make(User, first_name="CCCC", last_name="BBBB")
    test_crew_member_3 = baker.make(User, first_name="AAAA", last_name="BBBB")

    crew = [
        baker.make(
            "video_requests.CrewMember",
            member=test_crew_member_1,
            position="AAAA",
            request=video_request,
        ),
        baker.make(
            "video_requests.CrewMember",
            member=test_crew_member_1,
            position="BBBB",
            request=video_request,
        ),
        baker.make(
            "video_requests.CrewMember",
            member=test_crew_member_2,
            position="BBBB",
            request=video_request,
        ),
        baker.make(
            "video_requests.CrewMember",
            member=test_crew_member_2,
            position="CCCC",
            request=video_request,
        ),
        baker.make(
            "video_requests.CrewMember",
            member=test_crew_member_3,
            position="AAAA",
            request=video_request,
        ),
        baker.make(
            "video_requests.CrewMember",
            member=test_crew_member_3,
            position="CCCC",
            request=video_request,
        ),
    ]

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request:crew-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url, {"ordering": ordering})

    assert is_success(response.status_code)

    for i, _ in enumerate(crew):
        assert response.data[i]["id"] == crew[expected[i] - 1].id
