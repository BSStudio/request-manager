import pytest
from django.apps import apps
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_bakery import baker
from rest_framework.status import HTTP_200_OK, HTTP_302_FOUND

from tests.factories import make_user
from video_requests.models import Request, Todo

EVERY_MODEL = pytest.mark.parametrize(
    "model_name", ["comment", "crewmember", "rating", "request", "todo", "video"]
)


def make_one_of_each(user):
    video_request = baker.make(
        "video_requests.Request", requester=user, responsible=user
    )
    video = baker.make("video_requests.Video", request=video_request, editor=user)
    baker.make("video_requests.CrewMember", request=video_request, member=user)
    baker.make("video_requests.Comment", request=video_request, author=user)
    baker.make("video_requests.Rating", video=video, author=user)
    baker.make(
        "video_requests.Todo", request=video_request, video=video, creator=user
    ).assignees.add(user)


def count_queries(client, url, data=None):
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url, data)
    assert response.status_code == HTTP_200_OK
    return response, len(queries)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    ["comment", "crewmember", "rating", "request", "todo"],
)
def test_changelists_link_to_the_user_admin(client, model_name):
    # Every one of these lists renders a link to a user, so a hard coded admin
    # URL name would only break once the list is not empty.
    user = make_user(
        username="linked_user",
        first_name="Anna",
        last_name="Kovács",
        is_admin=True,
        is_superuser=True,
    )
    make_one_of_each(user)

    client.force_login(user)
    response = client.get(reverse(f"admin:video_requests_{model_name}_changelist"))

    assert response.status_code == HTTP_200_OK
    url = reverse("admin:common_user_change", args=(user.id,))
    assert f'<a href="{url}">Kovács Anna</a>' in response.content.decode()


@pytest.mark.django_db
def test_request_admin_keeps_who_added_the_request(client):
    admin = make_user(username="adding_admin", is_admin=True, is_superuser=True)
    requester = make_user(username="requester")
    form = {
        "title": "Added in the admin",
        "start_datetime_0": "2026-10-10",
        "start_datetime_1": "10:00:00",
        "end_datetime_0": "2026-10-10",
        "end_datetime_1": "12:00:00",
        "type": "Type",
        "place": "Place",
        "status": Request.Statuses.REQUESTED,
        "requester": requester.id,
        "additional_data": "{}",
        # Read-only in the admin: save_model() sets it on add, and an edit must
        # leave it alone.
        "requested_by": requester.id,
    }

    client.force_login(admin)
    added = client.post(reverse("admin:video_requests_request_add"), form)
    assert added.status_code == HTTP_302_FOUND
    video_request = Request.objects.get(title="Added in the admin")
    changed = client.post(
        reverse("admin:video_requests_request_change", args=(video_request.id,)),
        form,
    )

    assert changed.status_code == HTTP_302_FOUND
    video_request.refresh_from_db()
    assert video_request.requested_by == admin


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("model_name", "parent_fields"),
    [
        ("comment", {"request"}),
        ("crewmember", {"request"}),
        ("rating", {"video"}),
        ("todo", {"request", "video"}),
        ("video", {"request"}),
    ],
)
def test_admins_cannot_move_anything_to_another_parent(
    client, model_name, parent_fields
):
    user = make_user(username="moving_admin", is_admin=True, is_superuser=True)
    make_one_of_each(user)
    obj = apps.get_model("video_requests", model_name).objects.get()

    client.force_login(user)
    add_page = client.get(reverse(f"admin:video_requests_{model_name}_add"))
    change_page = client.get(
        reverse(f"admin:video_requests_{model_name}_change", args=(obj.id,))
    )

    assert parent_fields <= set(add_page.context["adminform"].form.fields)
    assert not parent_fields & set(change_page.context["adminform"].form.fields)


@pytest.mark.django_db
def test_todo_admin_rejects_a_video_of_another_request(client):
    admin = make_user(username="todo_admin", is_admin=True, is_superuser=True)
    video_request = baker.make("video_requests.Request", requester=admin)

    client.force_login(admin)
    response = client.post(
        reverse("admin:video_requests_todo_add"),
        {
            "request": video_request.id,
            "video": baker.make("video_requests.Video").id,
            "creator": admin.id,
            "description": "Cut the trailer",
            "status": Todo.Statuses.OPEN,
        },
    )

    assert response.status_code == HTTP_200_OK
    assert "video" in response.context["adminform"].form.errors
    assert not Todo.objects.exists()


@pytest.mark.django_db
@EVERY_MODEL
def test_changelists_can_be_searched(client, model_name):
    # Django resolves the search_fields lookups only once someone searches.
    user = make_user(username="searching_admin", is_admin=True, is_superuser=True)

    client.force_login(user)
    response = client.get(
        reverse(f"admin:video_requests_{model_name}_changelist"), {"q": "title"}
    )

    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
@EVERY_MODEL
def test_changelists_can_be_sorted_by_every_column(client, model_name):
    # Django resolves a column's ordering only once someone sorts by it.
    user = make_user(username="sorting_admin", is_admin=True, is_superuser=True)
    make_one_of_each(user)

    client.force_login(user)
    url = reverse(f"admin:video_requests_{model_name}_changelist")
    columns = client.get(url).context["cl"].list_display

    for index in range(len(columns)):
        assert client.get(url, {"o": index}).status_code == HTTP_200_OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("model_name", "column"), [("request", "num_of_videos"), ("video", "avg_rating")]
)
def test_changelists_can_be_sorted_by_computed_columns(client, model_name, column):
    # Sorting by a column without an ordering silently keeps the default one.
    user = make_user(username="sorting_admin", is_admin=True, is_superuser=True)

    client.force_login(user)
    url = reverse(f"admin:video_requests_{model_name}_changelist")
    changelist = client.get(url).context["cl"]

    assert changelist.get_ordering_field(column) == column


@pytest.mark.django_db
@pytest.mark.parametrize("model_name", ["request", "video"])
def test_admins_link_to_the_same_page_in_the_app(client, model_name):
    user = make_user(username="linking_admin", is_admin=True, is_superuser=True)
    make_one_of_each(user)
    obj = apps.get_model("video_requests", model_name).objects.get()

    client.force_login(user)
    response = client.get(
        reverse(f"admin:video_requests_{model_name}_change", args=(obj.id,))
    )

    assert f'href="{obj.admin_url}"' in response.content.decode()


@pytest.mark.django_db
@EVERY_MODEL
def test_changelists_run_as_many_queries_for_more_rows(client, model_name):
    user = make_user(username="counting_admin", is_admin=True, is_superuser=True)
    client.force_login(user)
    url = reverse(f"admin:video_requests_{model_name}_changelist")

    make_one_of_each(user)
    _, one_row = count_queries(client, url)
    make_one_of_each(user)
    response, two_rows = count_queries(client, url)

    assert response.context["cl"].result_count == 2
    assert two_rows == one_row


@pytest.mark.django_db
@EVERY_MODEL
def test_add_forms_run_as_many_queries_for_more_related_rows(client, model_name):
    user = make_user(username="counting_admin", is_admin=True, is_superuser=True)
    client.force_login(user)
    url = reverse(f"admin:video_requests_{model_name}_add")

    make_one_of_each(user)
    client.get(url)  # Fills Django's content type cache.
    _, one_each = count_queries(client, url)
    make_one_of_each(user)
    _, two_each = count_queries(client, url)

    assert two_each == one_each


@pytest.mark.django_db
# Autocompletes page through their results, which needs an ordered queryset.
@pytest.mark.filterwarnings("error::django.core.paginator.UnorderedObjectListWarning")
@pytest.mark.parametrize(
    ("model_name", "field_name"), [("rating", "video"), ("video", "request")]
)
def test_autocompletes_run_as_many_queries_for_more_results(
    client, model_name, field_name
):
    user = make_user(username="counting_admin", is_admin=True, is_superuser=True)
    client.force_login(user)
    url = reverse("admin:autocomplete")
    data = {
        "app_label": "video_requests",
        "model_name": model_name,
        "field_name": field_name,
    }

    make_one_of_each(user)
    _, one_result = count_queries(client, url, data)
    make_one_of_each(user)
    response, two_results = count_queries(client, url, data)

    assert len(response.json()["results"]) == 2
    assert two_results == one_result
