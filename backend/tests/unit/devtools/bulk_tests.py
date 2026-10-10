import pytest
from django.utils.timezone import localtime

from devtools.bulk import REQUEST_COUNT, create_bulk
from devtools.people import create_people
from video_requests.models import Request

pytestmark = pytest.mark.django_db

FINISHED = {
    Request.Statuses.DENIED,
    Request.Statuses.ARCHIVED,
    Request.Statuses.DONE,
    Request.Statuses.CANCELED,
    Request.Statuses.FAILED,
}


@pytest.fixture
def bulk():
    return create_bulk(create_people())


def test_creates_the_volume(bulk):
    assert len(bulk) == REQUEST_COUNT


def test_every_bulk_request_is_in_the_past_and_finished(bulk):
    requests = Request.objects.filter(pk__in=[request.pk for request in bulk])
    assert all(request.end_datetime < localtime() for request in requests)
    assert set(requests.values_list("status", flat=True)) == FINISHED


def test_finished_requests_have_videos(bulk):
    for request in Request.objects.filter(
        pk__in=[request.pk for request in bulk],
        status__in=[Request.Statuses.ARCHIVED, Request.Statuses.DONE],
    ):
        assert request.videos.exists()


def test_bulk_requesters_are_generated_people(bulk):
    fixed = {"minta.anna", "teszt.elek", "ures.peter", "tiltott.tamas"}
    assert not {request.requester.username for request in bulk} & fixed
