"""Ordering the ratings of one video."""

from datetime import datetime

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
        # Add created as secondary ordering field to make tests consistent.
        ("author__first_name,created", [2, 6, 1, 5, 3, 4]),
        ("author__last_name,created", [3, 4, 6, 5, 2, 1]),
        ("author__last_name,author__first_name,created", [6, 5, 3, 4, 2, 1]),
        ("created", [3, 4, 2, 6, 1, 5]),
        ("rating", [5, 3, 6, 2, 4, 1]),
        # Add created as secondary ordering field to make tests consistent.
        ("review,created", [3, 4, 2, 5, 6, 1]),
    ],
)
def test_order_ratings(admin_user, api_client, expected, ordering, time_machine):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)

    test_author_1 = baker.make(User, first_name="AAAA", last_name="CCCC")
    test_author_2 = baker.make(User, first_name="CCCC", last_name="BBBB")
    test_author_3 = baker.make(User, first_name="AAAA", last_name="BBBB")

    ratings = []

    time_machine.move_to(datetime(2014, 5, 20))
    ratings.append(
        baker.make(
            "video_requests.Rating",
            author=test_author_1,
            rating=5,
            review="CCC",
            video=video,
        )
    )

    time_machine.move_to(datetime(2000, 6, 27))
    ratings.append(
        baker.make("video_requests.Rating", author=test_author_1, rating=3, video=video)
    )

    time_machine.move_to(datetime(1987, 3, 30))
    ratings.append(
        baker.make("video_requests.Rating", author=test_author_2, rating=2, video=video)
    )

    time_machine.move_to(datetime(1992, 5, 11))
    ratings.append(
        baker.make("video_requests.Rating", author=test_author_2, rating=4, video=video)
    )

    time_machine.move_to(datetime(2020, 1, 20))
    ratings.append(
        baker.make(
            "video_requests.Rating",
            author=test_author_3,
            rating=1,
            review="AAA",
            video=video,
        )
    )

    time_machine.move_to(datetime(2005, 7, 21))
    ratings.append(
        baker.make(
            "video_requests.Rating",
            author=test_author_3,
            rating=2,
            review="BBB",
            video=video,
        )
    )

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.get(url, {"ordering": ordering})

    assert is_success(response.status_code)

    for i, _ in enumerate(ratings):
        assert response.data[i]["id"] == ratings[expected[i] - 1].id
