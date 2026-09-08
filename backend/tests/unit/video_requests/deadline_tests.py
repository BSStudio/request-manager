"""``recalculate_deadline``: moving an event moves an untouched deadline with it.

A pure function over the incoming payload, so these need no database at all.
"""

from datetime import timedelta

import pytest
from django.utils.timezone import localtime

from video_requests.models import Request
from video_requests.utilities import recalculate_deadline

AUTOMATIC_OFFSET = timedelta(weeks=3)

END = localtime().replace(microsecond=0)
NEW_END = END + timedelta(days=30)


def request_with(deadline):
    """An unsaved request, so nothing here touches the database."""
    return Request(
        start_datetime=END - timedelta(hours=2), end_datetime=END, deadline=deadline
    )


@pytest.fixture
def automatic():
    """A request whose deadline still sits where save() put it."""
    return request_with((END + AUTOMATIC_OFFSET).date())


def test_a_body_without_an_end_datetime_is_left_alone(automatic):
    assert recalculate_deadline(automatic, {"title": "Changed"}) == {"title": "Changed"}


def test_an_unchanged_end_datetime_is_left_alone(automatic):
    data = {"end_datetime": automatic.end_datetime}

    assert recalculate_deadline(automatic, data) == data


def test_moving_the_event_moves_an_automatic_deadline(automatic):
    data = recalculate_deadline(automatic, {"end_datetime": NEW_END})

    assert data["deadline"] == (NEW_END + AUTOMATIC_OFFSET).date()


def test_the_old_deadline_echoed_back_still_counts_as_untouched(automatic):
    # The admin dashboard sends the whole object back on a PUT.
    data = recalculate_deadline(
        automatic, {"end_datetime": NEW_END, "deadline": automatic.deadline}
    )

    assert data["deadline"] == (NEW_END + AUTOMATIC_OFFSET).date()


def test_a_deadline_the_caller_chose_is_kept(automatic):
    chosen = (NEW_END + timedelta(days=1)).date()

    data = recalculate_deadline(
        automatic, {"end_datetime": NEW_END, "deadline": chosen}
    )

    assert data["deadline"] == chosen


def test_a_hand_picked_existing_deadline_is_never_recalculated():
    # Somebody moved this deadline off the automatic offset on purpose.
    video_request = request_with((END + timedelta(days=5)).date())

    data = recalculate_deadline(video_request, {"end_datetime": NEW_END})

    assert "deadline" not in data
