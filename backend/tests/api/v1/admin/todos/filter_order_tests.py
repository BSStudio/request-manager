from datetime import datetime

import pytest
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from common.models import User
from tests.api.helpers import login
from video_requests.models import Todo

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "ordering,expected",
    [
        ("created", [3, 1, 4, 5, 6, 2]),
        ("status,created", [1, 4, 5, 3, 6, 2]),
    ],
)
def test_order_todos_on_request(
    admin_user, api_client, expected, ordering, time_machine
):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)

    todos = []

    time_machine.move_to(datetime(2001, 6, 15))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.OPEN,
            request=video_request,
            video=video,
        )
    )

    time_machine.move_to(datetime(2020, 11, 10))
    todos.append(
        baker.make(
            "video_requests.Todo", status=Todo.Statuses.CLOSED, request=video_request
        )
    )

    time_machine.move_to(datetime(1979, 12, 23))
    todos.append(
        baker.make(
            "video_requests.Todo", status=Todo.Statuses.CLOSED, request=video_request
        )
    )

    time_machine.move_to(datetime(2007, 5, 17))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.OPEN,
            request=video_request,
            video=video,
        )
    )

    time_machine.move_to(datetime(2007, 6, 4))
    todos.append(
        baker.make(
            "video_requests.Todo", status=Todo.Statuses.OPEN, request=video_request
        )
    )

    time_machine.move_to(datetime(2020, 5, 3))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.CLOSED,
            request=video_request,
            video=video,
        )
    )

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request:todo-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url, {"ordering": ordering})

    assert is_success(response.status_code)

    for i, _ in enumerate(todos):
        assert response.data[i]["id"] == todos[expected[i] - 1].id


@pytest.mark.parametrize(
    "ordering,expected",
    [
        ("created", [4, 6, 3, 1, 5, 2]),
        ("status,created", [4, 1, 5, 6, 3, 2]),
    ],
)
def test_order_todos_on_video(admin_user, api_client, expected, ordering, time_machine):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)

    todos = []

    time_machine.move_to(datetime(2002, 2, 10))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.OPEN,
            request=video_request,
            video=video,
        )
    )

    time_machine.move_to(datetime(2019, 3, 12))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.CLOSED,
            request=video_request,
            video=video,
        )
    )

    time_machine.move_to(datetime(1995, 2, 26))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.CLOSED,
            request=video_request,
            video=video,
        )
    )

    time_machine.move_to(datetime(1983, 9, 27))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.OPEN,
            request=video_request,
            video=video,
        )
    )

    time_machine.move_to(datetime(2015, 7, 24))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.OPEN,
            request=video_request,
            video=video,
        )
    )

    time_machine.move_to(datetime(1988, 11, 21))
    todos.append(
        baker.make(
            "video_requests.Todo",
            status=Todo.Statuses.CLOSED,
            request=video_request,
            video=video,
        )
    )

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request:video:todo-list",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.get(url, {"ordering": ordering})

    assert is_success(response.status_code)

    for i, _ in enumerate(todos):
        assert response.data[i]["id"] == todos[expected[i] - 1].id


"""
--------------------------------------------------
                    ALL TODOS
--------------------------------------------------
"""


@pytest.mark.parametrize("pagination", [True, False])
def test_filter_todos_by_status(admin_user, api_client, pagination):
    baker.make("video_requests.Todo", status=Todo.Statuses.OPEN, _quantity=3)
    baker.make("video_requests.Todo", status=Todo.Statuses.CLOSED, _quantity=5)

    login(api_client, admin_user)

    url = reverse("api:v1:admin:todos:todo-list")
    response_1 = api_client.get(
        url + f"?pagination={pagination}&status={Todo.Statuses.OPEN}"
    )
    response_2 = api_client.get(
        url + f"?pagination={pagination}&status={Todo.Statuses.CLOSED}"
    )
    response_3 = api_client.get(
        url
        + f"?pagination={pagination}&status={Todo.Statuses.OPEN}&status={Todo.Statuses.CLOSED}"
    )

    assert is_success(response_1.status_code)
    assert is_success(response_2.status_code)
    assert is_success(response_3.status_code)

    response_data_1 = response_1.data["results"] if pagination else response_1.data
    response_data_2 = response_2.data["results"] if pagination else response_2.data
    response_data_3 = response_3.data["results"] if pagination else response_3.data

    assert len(response_data_1) == 3
    assert len(response_data_2) == 5
    assert len(response_data_3) == 8


@pytest.mark.parametrize("pagination", [True, False])
def test_filter_todos_by_assignees(admin_user, api_client, pagination):
    users = baker.make(User, _quantity=4)
    baker.make("video_requests.Todo", assignees=[users[0], users[1]], _quantity=2)
    baker.make("video_requests.Todo", assignees=[users[2]], _quantity=3)
    baker.make("video_requests.Todo", assignees=[users[2], users[0]], _quantity=3)
    baker.make("video_requests.Todo", assignees=[users[3], users[1]], _quantity=1)
    baker.make("video_requests.Todo", assignees=[users[1]], _quantity=4)

    login(api_client, admin_user)

    url = reverse("api:v1:admin:todos:todo-list")
    response_1 = api_client.get(
        url + f"?pagination={pagination}&assignees={users[0].id}"
    )
    response_2 = api_client.get(
        url
        + f"?pagination={pagination}&assignees={users[2].id}&assignees={users[3].id}"
    )
    response_3 = api_client.get(
        url
        + f"?pagination={pagination}&assignees={users[0].id}&assignees={users[3].id}&assignees={users[1].id}"
    )

    assert is_success(response_1.status_code)
    assert is_success(response_2.status_code)
    assert is_success(response_3.status_code)

    response_data_1 = response_1.data["results"] if pagination else response_1.data
    response_data_2 = response_2.data["results"] if pagination else response_2.data
    response_data_3 = response_3.data["results"] if pagination else response_3.data

    assert len(response_data_1) == 5
    assert len(response_data_2) == 7
    assert len(response_data_3) == 10


@pytest.mark.parametrize(
    "ordering,expected",
    [
        ("created", [1, 6, 3, 2, 5, 4]),
        ("status,created", [1, 2, 5, 6, 3, 4]),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_order_todos(
    admin_user, api_client, expected, ordering, pagination, time_machine
):
    todos = []

    time_machine.move_to(datetime(1983, 4, 3))
    todos.append(baker.make("video_requests.Todo", status=Todo.Statuses.OPEN))

    time_machine.move_to(datetime(2009, 7, 18))
    todos.append(baker.make("video_requests.Todo", status=Todo.Statuses.OPEN))

    time_machine.move_to(datetime(1991, 12, 31))
    todos.append(baker.make("video_requests.Todo", status=Todo.Statuses.CLOSED))

    time_machine.move_to(datetime(2021, 12, 1))
    todos.append(baker.make("video_requests.Todo", status=Todo.Statuses.CLOSED))

    time_machine.move_to(datetime(2016, 10, 15))
    todos.append(baker.make("video_requests.Todo", status=Todo.Statuses.OPEN))

    time_machine.move_to(datetime(1988, 1, 18))
    todos.append(baker.make("video_requests.Todo", status=Todo.Statuses.CLOSED))

    login(api_client, admin_user)

    url = reverse("api:v1:admin:todos:todo-list")
    response = api_client.get(url, {"ordering": ordering, "pagination": pagination})

    assert is_success(response.status_code)

    for i, _ in enumerate(todos):
        response_data = response.data["results"] if pagination else response.data

        assert response_data[i]["id"] == todos[expected[i] - 1].id
