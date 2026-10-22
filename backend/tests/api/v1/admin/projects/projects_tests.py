from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.dateparse import parse_datetime
from django.utils.timezone import localtime
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    is_success,
)

from common.models import User
from tests.api.asserts import assert_exact_fields
from tests.api.helpers import do_login, get_response, login
from tests.api.matrix import staff_only
from video_requests.models import Project, Request
from video_requests.services import set_project

pytestmark = pytest.mark.django_db


def list_url():
    return reverse("api:v1:admin:projects:project-list")


def detail_url(project_id):
    return reverse("api:v1:admin:projects:project-detail", kwargs={"pk": project_id})


def make_request(project, days):
    return baker.make(
        "video_requests.Request",
        project=project,
        start_datetime=localtime() + timedelta(days=days),
    )


@staff_only(HTTP_200_OK)
def test_list_projects(api_client, expected, request, user):
    project = baker.make("video_requests.Project", responsible=baker.make(User))
    start = localtime() + timedelta(days=1)
    # Starts first and ends last, around a request that starts later.
    festival = baker.make(
        "video_requests.Request",
        project=project,
        start_datetime=start,
        end_datetime=start + timedelta(days=5),
    )
    make_request(project, 3)

    do_login(api_client, request, user)
    response = api_client.get(list_url())

    assert response.status_code == expected
    if is_success(response.status_code):
        [item] = response.data
        assert_exact_fields(
            item,
            [
                "first_start",
                "id",
                "last_end",
                "name",
                "request_count",
                "responsible",
            ],
        )
        assert_exact_fields(item["responsible"], ["avatar_url", "full_name", "id"])
        assert item["request_count"] == 2
        assert parse_datetime(item["first_start"]) == festival.start_datetime
        assert parse_datetime(item["last_end"]) == festival.end_datetime


def test_list_projects_newest_first(api_client, staff_user):
    past = baker.make("video_requests.Project", name="past")
    make_request(past, -10)
    future = baker.make("video_requests.Project", name="future")
    make_request(future, 5)
    baker.make("video_requests.Project", name="empty")

    login(api_client, staff_user)
    response = api_client.get(list_url())

    assert [item["name"] for item in response.data] == ["future", "empty", "past"]
    assert response.data[1]["first_start"] is None
    assert response.data[1]["last_end"] is None


@staff_only(HTTP_200_OK)
def test_retrieve_project(api_client, expected, request, user):
    project = baker.make("video_requests.Project")
    later = make_request(project, 3)
    sooner = make_request(project, 1)

    do_login(api_client, request, user)
    response = api_client.get(detail_url(project.id))

    assert response.status_code == expected
    if is_success(response.status_code):
        assert_exact_fields(response.data, ["id", "name", "requests", "responsible"])
        assert [item["id"] for item in response.data["requests"]] == [
            sooner.id,
            later.id,
        ]
        for item in response.data["requests"]:
            assert_exact_fields(
                item,
                [
                    "end_datetime",
                    "id",
                    "place",
                    "start_datetime",
                    "status",
                    "status_by_admin",
                    "title",
                    "type",
                ],
            )


@staff_only(HTTP_204_NO_CONTENT)
def test_destroy_project_keeps_its_requests(api_client, expected, request, user):
    project = baker.make("video_requests.Project")
    video_request = make_request(project, 1)

    do_login(api_client, request, user)
    response = api_client.delete(detail_url(project.id))

    assert response.status_code == expected
    if is_success(response.status_code):
        assert not Project.objects.exists()
        video_request.refresh_from_db()
        assert video_request.project is None
        assert video_request.history.latest().project_id is None
    else:
        assert Request.objects.get().project == project


@staff_only(HTTP_404_NOT_FOUND)
@pytest.mark.parametrize("method", ["GET", "DELETE", "PATCH"])
def test_missing_project(api_client, expected, method, missing_id, request, user):
    do_login(api_client, request, user)

    response = get_response(api_client, method, detail_url(missing_id), {})

    assert response.status_code == expected


@pytest.fixture
def new_row():
    def _new_row(**extra):
        start = localtime() + timedelta(days=1)
        return {
            "end_datetime": start + timedelta(hours=2),
            "place": "F épület, előadóterem",
            "start_datetime": start,
            "title": "Fizika 1 előadás",
            "type": "Előadás, rendezvény videós dokumentálása",
        } | extra

    return _new_row


def save(api_client, data, project=None):
    if project:
        return api_client.patch(detail_url(project.id), data, format="json")
    return api_client.post(list_url(), data, format="json")


def invalid_row(new_row):
    start = localtime() + timedelta(days=3)
    return new_row(start_datetime=start, end_datetime=start - timedelta(hours=1))


@staff_only({"POST": HTTP_201_CREATED, "PATCH": HTTP_200_OK})
@pytest.mark.parametrize("method", ["POST", "PATCH"])
def test_save_project_with_new_requests(
    api_client, expected, method, new_row, request, user
):
    responsible = baker.make(User, is_staff=True)
    project = baker.make("video_requests.Project") if method == "PATCH" else None

    user = do_login(api_client, request, user)
    response = save(
        api_client,
        {
            "name": "Fizika 1 előadások",
            "responsible": responsible.id,
            "new_requests": [
                new_row(responsible=responsible.id),
                new_row(responsible=responsible.id),
            ],
        },
        project,
    )

    assert response.status_code == expected[method]
    if is_success(response.status_code):
        assert_exact_fields(response.data, ["id", "name", "requests", "responsible"])
        assert response.data["name"] == "Fizika 1 előadások"
        assert response.data["responsible"]["id"] == responsible.id
        created = Request.objects.filter(project_id=response.data["id"])
        assert created.count() == 2
        for video_request in created:
            assert video_request.requested_by == user
            assert video_request.requester == user
            assert video_request.responsible == responsible
            assert video_request.status == Request.Statuses.REQUESTED
    else:
        assert not Request.objects.exists()


def test_new_requests_send_no_confirmation(
    api_client, django_capture_on_commit_callbacks, new_row, staff_user
):
    login(api_client, staff_user)

    with django_capture_on_commit_callbacks() as callbacks:
        response = save(
            api_client,
            {
                "name": "Kollégiumi hét",
                "new_requests": [
                    new_row(send_notification=True),
                    new_row(send_notification=True),
                ],
            },
        )

    assert response.status_code == HTTP_201_CREATED
    # A calendar event and a new request notification per request, and no
    # confirmation e-mail.
    assert len(callbacks) == 4


@pytest.mark.parametrize(
    ("caller", "status"),
    [
        ("admin_user", Request.Statuses.ACCEPTED),
        ("staff_user", Request.Statuses.REQUESTED),
    ],
)
def test_only_admins_create_accepted_requests(
    api_client, caller, new_row, request, status
):
    login(api_client, request.getfixturevalue(caller))

    response = save(
        api_client,
        {
            "name": "Fizika 1 előadások",
            "new_requests": [new_row(additional_data={"accepted": True})],
        },
    )

    assert response.status_code == HTTP_201_CREATED
    assert Request.objects.get().status == status


def test_one_bad_row_changes_nothing(api_client, new_row, staff_user):
    project = baker.make("video_requests.Project", name="Régi név")
    staying = make_request(project, 1)
    loose = make_request(None, 2)

    login(api_client, staff_user)
    response = save(
        api_client,
        {
            "name": "Új név",
            "add_requests": [loose.id],
            "remove_requests": [staying.id],
            "new_requests": [new_row(), new_row(), invalid_row(new_row)],
        },
        project,
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["new_requests"][:2] == [{}, {}]
    assert "end_datetime" in response.data["new_requests"][2]
    project.refresh_from_db()
    assert project.name == "Régi név"
    assert list(project.requests.all()) == [staying]
    assert Request.objects.count() == 2


def test_every_bad_row_is_reported(api_client, new_row, staff_user):
    login(api_client, staff_user)

    response = save(
        api_client,
        {
            "name": "Fizika 1 előadások",
            "new_requests": [
                new_row(),
                invalid_row(new_row),
                new_row(),
                invalid_row(new_row),
            ],
        },
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    errors = response.data["new_requests"]
    assert [bool(error) for error in errors] == [False, True, False, True]
    assert not Request.objects.exists()


@pytest.mark.parametrize("method", ["POST", "PATCH"])
def test_new_rows_need_every_required_field(api_client, method, new_row, staff_user):
    project = baker.make("video_requests.Project") if method == "PATCH" else None
    row = new_row()
    del row["end_datetime"]

    login(api_client, staff_user)
    response = save(
        api_client, {"name": "Fizika 1 előadások", "new_requests": [row]}, project
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    [error] = response.data["new_requests"][0]["end_datetime"]
    assert error.code == "required"


def test_one_bad_row_creates_no_project(api_client, new_row, staff_user):
    login(api_client, staff_user)

    response = save(
        api_client,
        {"name": "Kollégiumi hét", "new_requests": [new_row(), invalid_row(new_row)]},
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert not Project.objects.exists()
    assert not Request.objects.exists()


def test_add_requests_rejects_requests_of_another_project(api_client, staff_user):
    project, other = baker.make("video_requests.Project", _quantity=2)
    elsewhere = make_request(other, 1)

    login(api_client, staff_user)
    response = save(api_client, {"add_requests": [elsewhere.id]}, project)

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "add_requests" in response.data
    elsewhere.refresh_from_db()
    assert elsewhere.project == other


@pytest.mark.parametrize("creating", [False, True])
def test_remove_requests_needs_requests_of_this_project(
    api_client, creating, staff_user
):
    project = None if creating else baker.make("video_requests.Project")
    loose = make_request(None, 1)

    login(api_client, staff_user)
    response = save(
        api_client, {"name": "Kollégiumi hét", "remove_requests": [loose.id]}, project
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "remove_requests" in response.data


def test_adding_a_request_already_in_the_project_is_harmless(api_client, staff_user):
    project = baker.make("video_requests.Project")
    video_request = make_request(project, 1)

    login(api_client, staff_user)
    response = save(api_client, {"add_requests": [video_request.id]}, project)

    assert response.status_code == HTTP_200_OK
    video_request.refresh_from_db()
    assert video_request.project == project


def test_membership_changes_are_in_each_requests_history(api_client, staff_user):
    project = baker.make("video_requests.Project")
    video_request = make_request(None, 1)

    login(api_client, staff_user)
    save(api_client, {"add_requests": [video_request.id]}, project)
    assert video_request.history.latest().project_id == project.id

    save(api_client, {"remove_requests": [video_request.id]}, project)
    assert video_request.history.latest().project_id is None


def test_a_save_loads_the_requests_once(api_client, staff_user):
    project = baker.make("video_requests.Project")
    make_request(project, 1)

    login(api_client, staff_user)
    with CaptureQueriesContext(connection) as queries:
        response = save(api_client, {"name": "Új név"}, project)

    assert response.status_code == HTTP_200_OK
    loads = [
        query["sql"]
        for query in queries
        if 'FROM "video_requests_request"' in query["sql"]
        and '"project_id" IN' in query["sql"]
    ]
    assert len(loads) == 1


def test_an_assignment_made_elsewhere_survives_a_save(api_client, staff_user):
    project = baker.make("video_requests.Project")
    elsewhere = make_request(None, 1)
    added = make_request(None, 2)
    # For example from the request page, while the project editor is open.
    set_project(elsewhere, project)

    login(api_client, staff_user)
    response = save(
        api_client, {"add_requests": [added.id], "remove_requests": []}, project
    )

    assert response.status_code == HTTP_200_OK
    assert set(project.requests.all()) == {elsewhere, added}


def test_a_request_that_no_longer_validates_blocks_the_save(api_client, staff_user):
    project = baker.make("video_requests.Project", name="Régi név")
    legacy = make_request(None, 1)
    # Older data can break rules that came later; update() skips clean().
    Request.objects.filter(pk=legacy.pk).update(
        deadline=legacy.end_datetime.date() - timedelta(days=1)
    )

    login(api_client, staff_user)
    response = save(
        api_client, {"name": "Új név", "add_requests": [legacy.id]}, project
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "add_requests" in response.data
    project.refresh_from_db()
    assert project.name == "Régi név"
    legacy.refresh_from_db()
    assert legacy.project is None
