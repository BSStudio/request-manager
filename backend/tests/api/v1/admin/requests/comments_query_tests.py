"""Ordering the comments on one request."""

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
        ("author__first_name,created", [2, 5, 6, 1, 4, 3]),
        ("author__last_name,created", [4, 3, 5, 6, 2, 1]),
        ("author__last_name,author__first_name,created", [5, 6, 4, 3, 2, 1]),
        ("created", [2, 4, 3, 5, 6, 1]),
        ("internal", [1, 3, 5, 2, 4, 6]),
    ],
)
def test_order_comments(admin_user, api_client, expected, ordering, time_machine):
    video_request = baker.make("video_requests.Request")

    test_author_1 = baker.make(User, first_name="AAAA", last_name="CCCC")
    test_author_2 = baker.make(User, first_name="CCCC", last_name="BBBB")
    test_author_3 = baker.make(User, first_name="AAAA", last_name="BBBB")

    comments = []

    time_machine.move_to(datetime(2021, 4, 6))
    comments.append(
        baker.make(
            "video_requests.Comment",
            author=test_author_1,
            internal=False,
            request=video_request,
        )
    )

    time_machine.move_to(datetime(1985, 10, 26))
    comments.append(
        baker.make(
            "video_requests.Comment",
            author=test_author_1,
            internal=True,
            request=video_request,
        )
    )

    time_machine.move_to(datetime(2002, 7, 30))
    comments.append(
        baker.make(
            "video_requests.Comment",
            author=test_author_2,
            internal=False,
            request=video_request,
        )
    )

    time_machine.move_to(datetime(1998, 2, 12))
    comments.append(
        baker.make(
            "video_requests.Comment",
            author=test_author_2,
            internal=True,
            request=video_request,
        )
    )

    time_machine.move_to(datetime(2009, 12, 31))
    comments.append(
        baker.make(
            "video_requests.Comment",
            author=test_author_3,
            internal=False,
            request=video_request,
        )
    )

    time_machine.move_to(datetime(2012, 8, 2))
    comments.append(
        baker.make(
            "video_requests.Comment",
            author=test_author_3,
            internal=True,
            request=video_request,
        )
    )

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request:comment-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url, {"ordering": ordering})

    assert is_success(response.status_code)

    for i, _ in enumerate(comments):
        assert response.data[i]["id"] == comments[expected[i] - 1].id
