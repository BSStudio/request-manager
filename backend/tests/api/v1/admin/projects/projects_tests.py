from datetime import timedelta

import pytest
from django.utils.dateparse import parse_datetime
from django.utils.timezone import localtime
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    is_success,
)

from common.models import User
from tests.api.asserts import assert_exact_fields
from tests.api.helpers import do_login, get_response, login
from tests.api.matrix import staff_only
from video_requests.models import Project, Request

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
