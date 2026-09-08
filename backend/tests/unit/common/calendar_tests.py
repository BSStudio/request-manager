"""Mirroring accepted requests into the studio's Google Calendar.

Three Celery tasks, all of which no-op without a service account key file — which
is how the test and development environments run, and why none of this was
reachable from the API tests.
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.utils.timezone import localtime
from model_bakery import baker

from common.utilities import (
    MemoryCache,
    create_calendar_event,
    get_calendar_event_body,
    remove_calendar_event,
    update_calendar_event,
)

pytestmark = pytest.mark.django_db

EVENT_ID = "abc123"


@pytest.fixture
def video_request():
    start = localtime()
    return baker.make(
        "video_requests.Request",
        title="Test Request",
        place="Test place",
        start_datetime=start,
        end_datetime=start + timedelta(hours=2),
    )


@pytest.fixture
def calendar(settings):
    """A stand-in for the Google Calendar API, with a key file configured."""
    settings.GOOGLE_SERVICE_ACCOUNT_KEY_FILE_PATH = "/nonexistent/key.json"
    service = MagicMock()
    service.events().insert().execute.return_value = {"id": EVENT_ID}
    with patch("common.utilities.get_google_calendar_service", return_value=service):
        yield service.events()


class TestEventBody:
    def test_it_carries_what_the_crew_needs_to_find_the_shoot(self, video_request):
        body = get_calendar_event_body(video_request)

        assert body["summary"] == "Test Request"
        assert body["location"] == "Test place"
        assert video_request.admin_url in body["description"]
        assert body["start"] == {
            "dateTime": video_request.start_datetime.isoformat(),
            "timeZone": settings.TIME_ZONE,
        }
        assert body["end"] == {
            "dateTime": video_request.end_datetime.isoformat(),
            "timeZone": settings.TIME_ZONE,
        }


class TestWithoutCredentials:
    """The default in development and in tests: nothing must be called."""

    @pytest.fixture(autouse=True)
    def no_key_file(self, settings):
        settings.GOOGLE_SERVICE_ACCOUNT_KEY_FILE_PATH = None

    @pytest.mark.parametrize(
        "task", [create_calendar_event, update_calendar_event, remove_calendar_event]
    )
    def test_every_task_says_so_and_stops(self, task, video_request):
        with patch("common.utilities.get_google_calendar_service") as service:
            assert task(video_request.id) == (
                "Missing credentials file for Google Calendar"
            )

        service.assert_not_called()


class TestCreate:
    def test_it_stores_the_event_id_on_the_request(self, calendar, video_request):
        result = create_calendar_event(video_request.id)

        assert result == "Calendar event for Test Request was created successfully."
        video_request.refresh_from_db()
        assert video_request.additional_data["calendar_id"] == EVENT_ID
        assert calendar.insert.call_args.kwargs["calendarId"] == (
            settings.GOOGLE_CALENDAR_ID
        )


class TestUpdateAndRemove:
    @pytest.mark.parametrize(
        "task,verb,expected_call",
        [
            (update_calendar_event, "updated", "patch"),
            (remove_calendar_event, "deleted", "delete"),
        ],
    )
    def test_a_request_with_an_event_is_kept_in_step(
        self, calendar, expected_call, task, verb, video_request
    ):
        video_request.additional_data["calendar_id"] = EVENT_ID
        video_request.save()

        result = task(video_request.id)

        assert result == f"Calendar event for Test Request was {verb} successfully."
        call = getattr(calendar, expected_call)
        assert call.call_args.kwargs["eventId"] == EVENT_ID
        assert call.call_args.kwargs["calendarId"] == settings.GOOGLE_CALENDAR_ID

    @pytest.mark.parametrize("task", [update_calendar_event, remove_calendar_event])
    def test_a_request_that_never_reached_the_calendar_is_left_alone(
        self, calendar, task, video_request
    ):
        assert task(video_request.id) is None
        calendar.patch.assert_not_called()
        calendar.delete.assert_not_called()


class TestMemoryCache:
    """googleapiclient wants a discovery cache; this one is bounded."""

    @pytest.fixture(autouse=True)
    def empty(self):
        MemoryCache._CACHE.clear()
        yield
        MemoryCache._CACHE.clear()

    def test_what_goes_in_comes_back_out(self):
        cache = MemoryCache()
        cache.set("https://example.com/discovery", "content")

        assert cache.get("https://example.com/discovery") == "content"

    def test_a_url_never_stored_is_a_miss(self):
        assert MemoryCache().get("https://example.com/nothing") is None

    def test_it_evicts_the_oldest_entry_instead_of_growing(self):
        cache = MemoryCache()
        for index in range(MemoryCache._MAX_SIZE + 1):
            cache.set(f"url-{index}", index)

        assert len(MemoryCache._CACHE) == MemoryCache._MAX_SIZE
        assert cache.get("url-0") is None
        assert cache.get(f"url-{MemoryCache._MAX_SIZE}") == MemoryCache._MAX_SIZE
