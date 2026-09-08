import pytest
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
from video_requests.models import Todo

pytestmark = pytest.mark.django_db


def assert_response_keys(todo):
    assert_fields_exist(
        todo,
        [
            "assignees",
            "created",
            "creator",
            "description",
            "id",
            "request",
            "status",
            "video",
        ],
    )

    assert_fields_exist(todo.get("creator"), ["avatar_url", "full_name", "id"])
    assert_fields_exist(todo.get("request"), ["id", "title"])

    for assignee in todo.get("assignees"):
        assert_fields_exist(assignee, ["avatar_url", "full_name", "id"])

    video = todo.get("video")
    if video:
        assert_fields_exist(video, ["id", "title"])


@pytest.fixture
def todo_data():
    return {"description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}


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
def test_list_todos_on_request(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    todos = baker.make("video_requests.Todo", request=video_request, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:todo-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert len(response.data) == len(todos)
        for todo in response.data:
            assert_response_keys(todo)


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
def test_list_todos_on_video(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)
    todos = baker.make(
        "video_requests.Todo", request=video_request, video=video, _quantity=5
    )

    do_login(api_client, request, user)

    url_1 = reverse(
        "api:v1:admin:requests:request:todo-list",
        kwargs={"request_pk": video_request.id},
    )
    response_1 = api_client.get(url_1)

    url_2 = reverse(
        "api:v1:admin:requests:request:video:todo-list",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response_2 = api_client.get(url_2)

    assert response_1.status_code == expected
    assert response_2.status_code == expected

    if is_success(response_1.status_code) and is_success(response_2.status_code):
        assert len(response_1.data) == len(todos)
        assert len(response_2.data) == len(todos)
        for todo in response_1.data:
            assert_response_keys(todo)
        for todo in response_2.data:
            assert_response_keys(todo)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_201_CREATED),
        ("staff_user", HTTP_201_CREATED),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_todo_on_request_and_video(
    api_client, expected, request, todo_data, user
):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)

    user = do_login(api_client, request, user)

    urls = [
        reverse(
            "api:v1:admin:requests:request:todo-list",
            kwargs={"request_pk": video_request.id},
        ),
        reverse(
            "api:v1:admin:requests:request:video:todo-list",
            kwargs={"request_pk": video_request.id, "video_pk": video.id},
        ),
    ]

    for url in urls:
        number_of_todos_on_request = len(api_client.get(urls[0]).data)

        response = api_client.post(url, todo_data)

        assert response.status_code == expected

        if is_success(response.status_code):
            assert_response_keys(response.data)

            assert response.data["creator"]["avatar_url"] == user.avatar_url
            assert (
                response.data["creator"]["full_name"]
                == user.get_full_name_eastern_order()
            )
            assert response.data["creator"]["id"] == user.id

            assert response.data["description"] == todo_data["description"]

            response = api_client.get(url)

            assert response.status_code == HTTP_200_OK
            assert len(response.data) == 1

            # Make sure the created to-do is always available on the request as well
            response = api_client.get(urls[0])

            assert response.status_code == HTTP_200_OK
            assert len(response.data) == number_of_todos_on_request + 1


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_201_CREATED),
        ("staff_user", HTTP_201_CREATED),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_todo_all_fields_on_request_and_video(
    api_client, expected, request, todo_data, user
):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)
    users = baker.make(User, _fill_optional=True, _quantity=5)

    user = do_login(api_client, request, user)

    urls = [
        reverse(
            "api:v1:admin:requests:request:todo-list",
            kwargs={"request_pk": video_request.id},
        ),
        reverse(
            "api:v1:admin:requests:request:video:todo-list",
            kwargs={"request_pk": video_request.id, "video_pk": video.id},
        ),
    ]

    for url in urls:
        number_of_todos_on_request = len(api_client.get(urls[0]).data)

        response = api_client.post(
            url,
            todo_data
            | {
                "assignees": [user.id for user in users],
                "status": Todo.Statuses.CLOSED,
            },
        )

        assert response.status_code == expected

        if is_success(response.status_code):
            assert_response_keys(response.data)

            assert response.data["creator"]["avatar_url"] == user.avatar_url
            assert (
                response.data["creator"]["full_name"]
                == user.get_full_name_eastern_order()
            )
            assert response.data["creator"]["id"] == user.id

            assert response.data["description"] == todo_data["description"]

            for assignee in response.data["assignees"]:
                assert assignee["avatar_url"] in [user.avatar_url for user in users]
                assert assignee["full_name"] in [
                    user.get_full_name_eastern_order() for user in users
                ]
                assert assignee["id"] in [user.id for user in users]

            assert response.data["status"] == Todo.Statuses.CLOSED

            response = api_client.get(url)

            assert response.status_code == HTTP_200_OK
            assert len(response.data) == 1

            # Make sure the created to-do is always available on the request as well
            response = api_client.get(urls[0])

            assert response.status_code == HTTP_200_OK
            assert len(response.data) == number_of_todos_on_request + 1


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
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_list_create_todos_error_on_request(
    api_client,
    expected,
    method,
    not_existing_request_id,
    request,
    todo_data,
    user,
):
    video_request = baker.make("video_requests.Request")
    baker.make("video_requests.Todo", request=video_request, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:todo-list",
        kwargs={"request_pk": not_existing_request_id},
    )

    response = get_response(api_client, method, url, todo_data)

    assert response.status_code == expected


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
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_list_create_todos_error_on_video(
    api_client,
    expected,
    method,
    not_existing_request_id,
    not_existing_video_id,
    request,
    todo_data,
    user,
):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)
    baker.make("video_requests.Todo", request=video_request, video=video, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video:todo-list",
        kwargs={"request_pk": video_request.id, "video_pk": not_existing_video_id},
    )

    response = get_response(api_client, method, url, todo_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:admin:requests:request:video:todo-list",
        kwargs={"request_pk": not_existing_request_id, "video_pk": video.id},
    )

    response = get_response(api_client, method, url, todo_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:admin:requests:request:video:todo-list",
        kwargs={
            "request_pk": not_existing_request_id,
            "video_pk": not_existing_video_id,
        },
    )

    response = get_response(api_client, method, url, todo_data)

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
def test_create_todos_validation_on_request_and_video(
    api_client, expected, request, user
):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)

    do_login(api_client, request, user)

    urls = [
        reverse(
            "api:v1:admin:requests:request:todo-list",
            kwargs={"request_pk": video_request.id},
        ),
        reverse(
            "api:v1:admin:requests:request:video:todo-list",
            kwargs={"request_pk": video_request.id, "video_pk": video.id},
        ),
    ]

    for url in urls:
        response = api_client.post(url, {"description": ""})
        assert response.status_code == expected
        if response.status_code == HTTP_400_BAD_REQUEST:
            assert response.data["description"][0] == ErrorDetail(
                "This field may not be blank.", code="blank"
            )

        response = api_client.post(url, {"description": None})
        assert response.status_code == expected
        if response.status_code == HTTP_400_BAD_REQUEST:
            assert response.data["description"][0] == ErrorDetail(
                "This field may not be null.", code="null"
            )

        response = api_client.post(url, {"status": 42069})
        assert response.status_code == expected
        if response.status_code == HTTP_400_BAD_REQUEST:
            assert response.data["status"][0] == ErrorDetail(
                string='"42069" is not a valid choice.', code="invalid_choice"
            )

        response = api_client.post(url, {"assignees": [42069]})
        assert response.status_code == expected
        if response.status_code == HTTP_400_BAD_REQUEST:
            assert response.data["assignees"][0] == ErrorDetail(
                string='Invalid pk "42069" - object does not exist.',
                code="does_not_exist",
            )


"""
--------------------------------------------------
                    ALL TODOS
--------------------------------------------------
"""


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
def test_list_all_todos(api_client, expected, pagination, request, user):
    video_requests = baker.make("video_requests.Request", _quantity=5)
    videos = []
    todos = []

    for video_request in video_requests:
        videos.extend(
            baker.make("video_requests.Video", request=video_request, _quantity=2)
        )

    for video_request in video_requests:
        todos.extend(
            baker.make("video_requests.Todo", request=video_request, _quantity=3)
        )

    for video in videos:
        todos.extend(
            baker.make(
                "video_requests.Todo", request=video.request, video=video, _quantity=2
            )
        )

    do_login(api_client, request, user)

    url = reverse("api:v1:admin:todos:todo-list")
    response = api_client.get(url, {"pagination": pagination})

    assert response.status_code == expected

    if is_success(response.status_code):
        if pagination:
            assert_fields_exist(
                response.data, ["count", "links", "results", "total_pages"]
            )
            assert_fields_exist(response.data["links"], ["next", "previous"])

            assert response.data["count"] == len(todos)

        response_data = response.data["results"] if pagination else response.data

        assert len(response_data) == len(todos)
        for todo in response_data:
            assert_response_keys(todo)


@pytest.mark.parametrize(
    "user,expected",
    [
        (
            "admin_user",
            {
                "DELETE": HTTP_204_NO_CONTENT,
                "GET": HTTP_200_OK,
                "PATCH": HTTP_200_OK,
                "PUT": HTTP_200_OK,
            },
        ),
        (
            "staff_user",
            {
                "DELETE": HTTP_403_FORBIDDEN,
                "GET": HTTP_200_OK,
                "PATCH": HTTP_200_OK,
                "PUT": HTTP_200_OK,
            },
        ),
        (
            "basic_user",
            {
                "DELETE": HTTP_403_FORBIDDEN,
                "GET": HTTP_403_FORBIDDEN,
                "PATCH": HTTP_403_FORBIDDEN,
                "PUT": HTTP_403_FORBIDDEN,
            },
        ),
        (
            "service_account",
            {
                "DELETE": HTTP_403_FORBIDDEN,
                "GET": HTTP_403_FORBIDDEN,
                "PATCH": HTTP_403_FORBIDDEN,
                "PUT": HTTP_403_FORBIDDEN,
            },
        ),
        (
            None,
            {
                "DELETE": HTTP_401_UNAUTHORIZED,
                "GET": HTTP_401_UNAUTHORIZED,
                "PATCH": HTTP_401_UNAUTHORIZED,
                "PUT": HTTP_401_UNAUTHORIZED,
            },
        ),
    ],
)
@pytest.mark.parametrize("method", ["DELETE", "GET", "PATCH", "PUT"])
def test_retrieve_update_destroy_todo(
    api_client, expected, method, request, todo_data, user
):
    video_request = baker.make("video_requests.Request")
    todo = baker.make("video_requests.Todo", request=video_request)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:todos:todo-detail",
        kwargs={"pk": todo.id},
    )
    response = get_response(api_client, method, url, todo_data)

    assert response.status_code == expected[method]

    if is_success(response.status_code) and method != "DELETE":
        assert_response_keys(response.data)

        if method in ["PATCH", "PUT"]:
            assert response.data["description"] == todo_data["description"]


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
def test_destroy_todo_created_by_user(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request")
    todo = baker.make("video_requests.Todo", creator=user, request=video_request)

    url = reverse(
        "api:v1:admin:todos:todo-detail",
        kwargs={"pk": todo.id},
    )
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
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_todo_all_fields(api_client, expected, method, request, todo_data, user):
    video_request = baker.make("video_requests.Request")
    todo = baker.make("video_requests.Todo", request=video_request)
    users = baker.make(User, _fill_optional=True, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:todos:todo-detail",
        kwargs={"pk": todo.id},
    )
    response = get_response(
        api_client,
        method,
        url,
        todo_data
        | {"assignees": [user.id for user in users], "status": Todo.Statuses.CLOSED},
    )

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)

        assert response.data["description"] == todo_data["description"]

        for assignee in response.data["assignees"]:
            assert assignee["avatar_url"] in [user.avatar_url for user in users]
            assert assignee["full_name"] in [
                user.get_full_name_eastern_order() for user in users
            ]
            assert assignee["id"] in [user.id for user in users]

        assert response.data["status"] == Todo.Statuses.CLOSED


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
@pytest.mark.parametrize("method", ["DELETE", "GET", "PATCH", "PUT"])
def test_retrieve_update_destroy_todo_error(
    api_client, expected, method, not_existing_todo_id, request, todo_data, user
):
    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:todos:todo-detail",
        kwargs={"pk": not_existing_todo_id},
    )
    response = get_response(api_client, method, url, todo_data)

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
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_todo_validation(api_client, expected, method, request, user):
    video_request = baker.make("video_requests.Request")
    todo = baker.make("video_requests.Todo", request=video_request)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:todos:todo-detail",
        kwargs={"pk": todo.id},
    )

    response = get_response(api_client, method, url, {"description": ""})
    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["description"][0] == ErrorDetail(
            "This field may not be blank.", code="blank"
        )

    response = get_response(api_client, method, url, {"description": None})
    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["description"][0] == ErrorDetail(
            "This field may not be null.", code="null"
        )

    response = get_response(api_client, method, url, {"status": 42069})
    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["status"][0] == ErrorDetail(
            string='"42069" is not a valid choice.', code="invalid_choice"
        )

    response = get_response(api_client, method, url, {"assignees": [42069]})
    assert response.status_code == expected
    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["assignees"][0] == ErrorDetail(
            string='Invalid pk "42069" - object does not exist.', code="does_not_exist"
        )
