from datetime import date, datetime, timedelta

import pytest
from django.utils.timezone import make_aware
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from common.models import User
from tests.api.helpers import login
from video_requests.models import Request, Video

pytestmark = pytest.mark.django_db

"""
--------------------------------------------------
                    COMMENTS
--------------------------------------------------
"""


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


"""
--------------------------------------------------
                      CREW
--------------------------------------------------
"""


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


"""
--------------------------------------------------
                    RATINGS
--------------------------------------------------
"""


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


"""
--------------------------------------------------
                    REQUESTS
--------------------------------------------------
"""


@pytest.mark.parametrize(
    "filters,expected",
    [
        ({"deadline_after": "2003-08-25"}, 5),
        ({"deadline_before": "2009-10-03"}, 3),
        (
            {
                "deadline_after": "2008-03-02",
                "deadline_before": "2015-04-05",
            },
            3,
        ),
        ({"start_datetime_after": "2007-08-25"}, 4),
        ({"start_datetime_before": "2012-01-01"}, 4),
        (
            {
                "start_datetime_after": "2005-01-01",
                "start_datetime_before": "2012-01-01",
            },
            2,
        ),
        ({"status": Request.Statuses.REQUESTED}, 1),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_filter_requests(admin_user, api_client, filters, expected, pagination):
    values = [
        ("1993-10-29", Request.Statuses.CANCELED),
        ("2004-12-10", Request.Statuses.DONE),
        ("2008-03-02", Request.Statuses.UPLOADED),
        ("2009-10-03", Request.Statuses.REQUESTED),
        ("2015-03-12", Request.Statuses.EDITED),
        ("2022-11-25", Request.Statuses.DENIED),
    ]

    requests = []

    for start_date, status in values:
        start_datetime = make_aware(
            datetime.combine(date.fromisoformat(start_date), datetime.min.time())
        )
        end_datetime = start_datetime + timedelta(hours=3)
        requests.append(
            baker.make(
                "video_requests.Request",
                end_datetime=end_datetime,
                status=status,
                start_datetime=start_datetime,
            )
        )

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(url, {"pagination": pagination} | filters)

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == expected


@pytest.mark.parametrize("pagination", [True, False])
def test_filter_requests_multiple_status(admin_user, api_client, pagination):
    baker.make("video_requests.Request", status=Request.Statuses.UPLOADED),
    baker.make("video_requests.Request", status=Request.Statuses.ACCEPTED),
    baker.make("video_requests.Request", status=Request.Statuses.ARCHIVED),
    baker.make("video_requests.Request", status=Request.Statuses.FAILED),
    baker.make("video_requests.Request", status=Request.Statuses.RECORDED),
    baker.make("video_requests.Request", status=Request.Statuses.CANCELED),

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(
        url
        + f"?pagination={pagination}&status={Request.Statuses.RECORDED}&status={Request.Statuses.ACCEPTED}"
    )

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 2


@pytest.mark.parametrize(
    "ordering,expected",
    [
        ("created", [6, 2, 3, 1, 5, 4]),
        ("deadline", [4, 6, 2, 3, 1, 5]),
        # There can be a difference in ordering of similar object if pagination is enabled.
        # Add created as secondary ordering field to make tests consistent.
        ("responsible__first_name,created", [6, 2, 5, 3, 1, 4]),
        ("responsible__last_name,created", [6, 3, 5, 2, 1, 4]),
        ("responsible__last_name,responsible__first_name,created", [6, 5, 3, 2, 1, 4]),
        ("start_datetime", [4, 6, 2, 3, 1, 5]),
        ("status", [3, 6, 2, 4, 1, 5]),
        ("title", [2, 4, 1, 3, 6, 5]),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_order_requests(
    admin_user, api_client, expected, ordering, pagination, time_machine
):
    test_responsible_1 = baker.make(User, first_name="AAAA", last_name="CCCC")
    test_responsible_2 = baker.make(User, first_name="CCCC", last_name="BBBB")
    test_responsible_3 = baker.make(User, first_name="AAAA", last_name="BBBB")

    requests = []

    start_date = make_aware(
        datetime.combine(date.fromisoformat("2023-05-30"), datetime.min.time())
    )

    time_machine.move_to(datetime(2006, 3, 16))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=3),
            start_datetime=start_date - timedelta(days=4),
            status=Request.Statuses.DONE,
            title="CCCC",
        )
    )

    time_machine.move_to(datetime(1999, 6, 14))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=9),
            responsible=test_responsible_1,
            start_datetime=start_date - timedelta(days=10),
            status=Request.Statuses.RECORDED,
            title="AAAA",
        )
    )

    time_machine.move_to(datetime(2003, 12, 17))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=7),
            responsible=test_responsible_2,
            start_datetime=start_date - timedelta(days=8),
            status=Request.Statuses.DENIED,
            title="DDDD",
        )
    )

    time_machine.move_to(datetime(2023, 6, 16))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=14),
            start_datetime=start_date - timedelta(days=15),
            status=Request.Statuses.UPLOADED,
            title="BBBB",
        )
    )

    time_machine.move_to(datetime(2020, 12, 25))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=1),
            responsible=test_responsible_3,
            start_datetime=start_date - timedelta(days=2),
            status=Request.Statuses.CANCELED,
            title="FFFF",
        )
    )

    time_machine.move_to(datetime(1999, 2, 8))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=12),
            responsible=test_responsible_3,
            start_datetime=start_date - timedelta(days=13),
            status=Request.Statuses.ACCEPTED,
            title="EEEE",
        )
    )

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(url, {"ordering": ordering, "pagination": pagination})

    assert is_success(response.status_code)

    for i, _ in enumerate(requests):
        response_data = response.data["results"] if pagination else response.data

        assert response_data[i]["id"] == requests[expected[i] - 1].id


@pytest.mark.parametrize("pagination", [True, False])
def test_search_requests(admin_user, api_client, pagination):
    requests = [
        baker.make("video_requests.Request", title="AAAA BBBB CCCC"),
        baker.make("video_requests.Request", title="BBBB AAAA CCCC"),
        baker.make("video_requests.Request", title="CCCC BBBB AAAA"),
        baker.make("video_requests.Request", title="BBCC CCAA AABB"),
        baker.make("video_requests.Request", title="BBBB CCCC BBBB"),
    ]

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(url, {"pagination": pagination, "search": "AAAA"})

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 3

    assert response_data[0]["id"] == requests[0].id
    assert response_data[1]["id"] == requests[1].id
    assert response_data[2]["id"] == requests[2].id


"""
--------------------------------------------------
                     VIDEOS
--------------------------------------------------
"""


@pytest.mark.parametrize(
    "ordering,expected",
    [
        # Add title as secondary ordering field to make tests consistent.
        ("avg_rating,title", [1, 5, 4, 6, 2, 3]),
        ("editor__first_name,title", [1, 6, 5, 4, 2, 3]),
        ("editor__last_name,title", [6, 4, 5, 1, 2, 3]),
        ("editor__last_name,editor__first_name,title", [6, 5, 4, 1, 2, 3]),
        ("status", [2, 6, 5, 3, 1, 4]),
        ("title", [1, 6, 2, 4, 3, 5]),
    ],
)
def test_order_videos(admin_user, api_client, expected, ordering):
    video_request = baker.make("video_requests.Request")

    test_editor_1 = baker.make(User, first_name="AAAA", last_name="CCCC")
    test_editor_2 = baker.make(User, first_name="CCCC", last_name="BBBB")
    test_editor_3 = baker.make(User, first_name="AAAA", last_name="BBBB")

    videos = [
        baker.make(
            "video_requests.Video",
            editor=test_editor_1,
            request=video_request,
            status=Video.Statuses.PUBLISHED,
            title="AAAA1",
        ),
        baker.make(
            "video_requests.Video",
            request=video_request,
            status=Video.Statuses.PENDING,
            title="BBBB1",
        ),
        baker.make(
            "video_requests.Video",
            request=video_request,
            status=Video.Statuses.CODED,
            title="CCCC1",
        ),
        baker.make(
            "video_requests.Video",
            editor=test_editor_2,
            request=video_request,
            status=Video.Statuses.DONE,
            title="BBBB2",
        ),
        baker.make(
            "video_requests.Video",
            editor=test_editor_3,
            request=video_request,
            status=Video.Statuses.EDITED,
            title="CCCC2",
        ),
        baker.make(
            "video_requests.Video",
            editor=test_editor_3,
            request=video_request,
            status=Video.Statuses.IN_PROGRESS,
            title="AAAA2",
        ),
    ]

    # Avg rating: 2 (Video 1)
    baker.make("video_requests.Rating", rating=1, video=videos[0])
    baker.make("video_requests.Rating", rating=2, video=videos[0])
    baker.make("video_requests.Rating", rating=3, video=videos[0])

    # Avg rating: 3,3 (Video 4)
    baker.make("video_requests.Rating", rating=5, video=videos[3])
    baker.make("video_requests.Rating", rating=2, video=videos[3])
    baker.make("video_requests.Rating", rating=3, video=videos[3])

    # Avg rating: 3 (Video 5)
    baker.make("video_requests.Rating", rating=4, video=videos[4])
    baker.make("video_requests.Rating", rating=4, video=videos[4])
    baker.make("video_requests.Rating", rating=1, video=videos[4])

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request:video-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url, {"ordering": ordering})

    assert is_success(response.status_code)

    for i, _ in enumerate(videos):
        assert response.data[i]["id"] == videos[expected[i] - 1].id


"""
--------------------------------------------------
                   ALL VIDEOS
--------------------------------------------------
"""


@pytest.mark.parametrize(
    "filters,expected",
    [
        ({"last_aired": "2023-05-01"}, 5),
        ({"length_max": 60}, 4),
        ({"length_min": 60}, 3),
        (
            {
                "length_max": 100,
                "length_min": 60,
            },
            2,
        ),
        ({"request_start_datetime_after": "2021-11-13"}, 3),
        ({"request_start_datetime_before": "2021-11-15"}, 5),
        (
            {
                "request_start_datetime_after": "2021-11-13",
                "request_start_datetime_before": "2021-11-15",
            },
            2,
        ),
        ({"status": Video.Statuses.EDITED}, 1),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_filter_all_videos(admin_user, api_client, filters, expected, pagination):
    start_datetime = make_aware(
        datetime.combine(date.fromisoformat("2021-11-21"), datetime.min.time())
    )

    video_requests = [
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=15)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=1)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=21)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=7)
        ),
    ]

    baker.make(
        "video_requests.Video",
        additional_data={"length": 600},
        request=video_requests[2],
        status=Video.Statuses.PENDING,
        title="AAAA1",
    ),
    baker.make(
        "video_requests.Video",
        additional_data={"aired": ["2023-04-01"]},
        request=video_requests[3],
        status=Video.Statuses.CODED,
        title="BBBB1",
    ),
    baker.make(
        "video_requests.Video",
        request=video_requests[0],
        status=Video.Statuses.EDITED,
        title="CCCC1",
    ),
    baker.make(
        "video_requests.Video",
        additional_data={"aired": ["2023-01-21", "2012-01-10"], "length": 60},
        request=video_requests[1],
        status=Video.Statuses.DONE,
        title="BBBB2",
    ),
    baker.make(
        "video_requests.Video",
        additional_data={
            "aired": ["2023-05-30", "2012-01-10", "2008-11-25"],
            "length": 100,
        },
        request=video_requests[0],
        status=Video.Statuses.PUBLISHED,
        title="CCCC2",
    ),
    baker.make(
        "video_requests.Video",
        request=video_requests[3],
        status=Video.Statuses.IN_PROGRESS,
        title="AAAA2",
    ),

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(url, {"pagination": pagination} | filters)

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == expected


@pytest.mark.parametrize("pagination", [True, False])
def test_filter_all_videos_multiple_status(admin_user, api_client, pagination):
    video_requests = baker.make("video_requests.Request", _quantity=4)

    baker.make(
        "video_requests.Video", request=video_requests[1], status=Video.Statuses.PENDING
    ),
    baker.make(
        "video_requests.Video",
        request=video_requests[3],
        status=Video.Statuses.PUBLISHED,
    ),
    baker.make(
        "video_requests.Video", request=video_requests[1], status=Video.Statuses.DONE
    ),
    baker.make(
        "video_requests.Video",
        request=video_requests[2],
        status=Video.Statuses.IN_PROGRESS,
    ),
    baker.make(
        "video_requests.Video", request=video_requests[2], status=Video.Statuses.EDITED
    ),
    baker.make(
        "video_requests.Video", request=video_requests[0], status=Video.Statuses.CODED
    ),

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(
        url
        + f"?pagination={pagination}&status={Video.Statuses.CODED}&status={Video.Statuses.PUBLISHED}"
    )

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 2


@pytest.mark.parametrize(
    "ordering,expected",
    [
        # Add title as secondary ordering field to make tests consistent.
        ("avg_rating,title", [6, 3, 2, 1, 4, 5]),
        ("last_aired,title", [6, 4, 1, 2, 3, 5]),
        ("length,title", [6, 1, 3, 2, 4, 5]),
        ("request__start_datetime,title", [4, 6, 2, 1, 3, 5]),
        ("status", [2, 6, 5, 3, 1, 4]),
        ("title", [1, 6, 2, 4, 3, 5]),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_order_all_videos(admin_user, api_client, expected, ordering, pagination):
    start_datetime = make_aware(
        datetime.combine(date.fromisoformat("2023-05-30"), datetime.min.time())
    )

    video_request = [
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=1)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=8)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=3)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=7)
        ),
    ]

    videos = [
        baker.make(
            "video_requests.Video",
            additional_data={
                "aired": ["2023-05-30", "2012-01-10", "2008-11-25"],
                "length": 100,
            },
            request=video_request[2],
            status=Video.Statuses.PUBLISHED,
            title="AAAA1",
        ),
        baker.make(
            "video_requests.Video",
            request=video_request[3],
            status=Video.Statuses.PENDING,
            title="BBBB1",
        ),
        baker.make(
            "video_requests.Video",
            additional_data={"length": 600},
            request=video_request[0],
            status=Video.Statuses.CODED,
            title="CCCC1",
        ),
        baker.make(
            "video_requests.Video",
            additional_data={"aired": ["2023-04-01"]},
            request=video_request[1],
            status=Video.Statuses.DONE,
            title="BBBB2",
        ),
        baker.make(
            "video_requests.Video",
            request=video_request[0],
            status=Video.Statuses.EDITED,
            title="CCCC2",
        ),
        baker.make(
            "video_requests.Video",
            additional_data={"aired": ["2023-01-21", "2012-01-10"], "length": 60},
            request=video_request[3],
            status=Video.Statuses.IN_PROGRESS,
            title="AAAA2",
        ),
    ]

    # Avg rating: 4,3 (Video 2)
    baker.make("video_requests.Rating", rating=5, video=videos[1])
    baker.make("video_requests.Rating", rating=5, video=videos[1])
    baker.make("video_requests.Rating", rating=3, video=videos[1])

    # Avg rating: 4 (Video 3)
    baker.make("video_requests.Rating", rating=4, video=videos[2])
    baker.make("video_requests.Rating", rating=4, video=videos[2])
    baker.make("video_requests.Rating", rating=4, video=videos[2])

    # Avg rating: 2,3 (Video 6)
    baker.make("video_requests.Rating", rating=2, video=videos[5])
    baker.make("video_requests.Rating", rating=2, video=videos[5])
    baker.make("video_requests.Rating", rating=3, video=videos[5])

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(url, {"ordering": ordering, "pagination": pagination})

    assert is_success(response.status_code)

    for i, _ in enumerate(videos):
        response_data = response.data["results"] if pagination else response.data

        assert response_data[i]["id"] == videos[expected[i] - 1].id


@pytest.mark.parametrize("pagination", [True, False])
def test_search_all_videos(admin_user, api_client, pagination):
    video_requests = baker.make("video_requests.Request", _quantity=4)

    videos = [
        baker.make(
            "video_requests.Video", request=video_requests[0], title="AAAA BBBB CCCC"
        ),
        baker.make(
            "video_requests.Video", request=video_requests[2], title="BBBB CCCC BBBB"
        ),
        baker.make(
            "video_requests.Video", request=video_requests[0], title="BBCC CCAA AABB"
        ),
        baker.make(
            "video_requests.Video", request=video_requests[3], title="BBBB AAAA CCCC"
        ),
        baker.make(
            "video_requests.Video", request=video_requests[1], title="CCCC BBBB AAAA"
        ),
    ]

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(
        url, {"ordering": "title", "pagination": pagination, "search": "AAAA"}
    )

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 3

    assert response_data[0]["id"] == videos[0].id
    assert response_data[1]["id"] == videos[3].id
    assert response_data[2]["id"] == videos[4].id
