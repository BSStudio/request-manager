from datetime import timedelta

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from model_bakery import baker

pytestmark = pytest.mark.django_db


@pytest.fixture
def video_request():
    return baker.make("video_requests.Request")


@pytest.fixture
def video(video_request):
    return baker.make("video_requests.Video", request=video_request)


class TestStringRepresentations:

    def test_request(self, video_request):
        assert (
            str(video_request)
            == f"{video_request.title} || {video_request.start_datetime.date()}"
        )

    def test_crew_member(self, video_request):
        crew_member = baker.make("video_requests.CrewMember", request=video_request)

        assert str(crew_member) == (
            f"{video_request.title} || "
            f"{crew_member.member.get_full_name_eastern_order()} - "
            f"{crew_member.position}"
        )

    def test_video(self, video, video_request):
        assert str(video) == f"{video_request.title} || {video.title}"

    def test_comment(self, video_request):
        comment = baker.make("video_requests.Comment", request=video_request)

        assert str(comment) == (
            f"{video_request.title} || {comment.text} - "
            f"{comment.author.get_full_name_eastern_order()}"
        )

    def test_rating(self, video):
        rating = baker.make("video_requests.Rating", video=video)

        assert str(rating) == (
            f"{video.title} || {rating.author.get_full_name_eastern_order()} "
            f"({rating.rating})"
        )

    def test_todo(self, video_request):
        todo = baker.make(
            "video_requests.Todo",
            request=video_request,
            description="Test todo",
        )

        assert str(todo) == f"Todo || {video_request.title} - Test todo[...]"


class TestRequestUrls:
    def test_url_points_at_the_requester_facing_page(self, video_request):
        assert video_request.url == (
            f"{settings.BASE_URL}/my-requests/{video_request.id}"
        )

    def test_admin_url_points_at_the_dashboard(self, video_request):
        assert video_request.admin_url == (
            f"{settings.BASE_URL}/admin/requests/{video_request.id}"
        )


class TestVideoAdminUrl:
    def test_points_at_the_dashboard(self, video, video_request):
        assert video.admin_url == (
            f"{settings.BASE_URL}/admin/requests/{video_request.id}/videos/{video.id}"
        )


class TestVideoPublishedUrl:
    def test_is_none_until_the_video_is_published(self, video):
        assert video.published_url is None

    def test_comes_from_the_publishing_data(self, video):
        video.additional_data["publishing"] = {"website": "https://example.com"}
        video.save()

        assert video.published_url == "https://example.com"


class TestRequestValidation:
    def test_a_freshly_built_request_is_valid(self, video_request):
        video_request.refresh_from_db()
        video_request.full_clean()  # Should not raise

    def test_the_event_cannot_end_before_it_starts(self, video_request):
        video_request.end_datetime = video_request.start_datetime - timedelta(hours=5)

        with pytest.raises(ValidationError) as error:
            video_request.full_clean()

        assert error.value.messages[0] == "Must be later than the start of the event."

    def test_the_deadline_cannot_fall_on_or_before_the_event(self, video_request):
        video_request.deadline = video_request.end_datetime.date()

        with pytest.raises(ValidationError) as error:
            video_request.full_clean()

        assert error.value.messages[0] == "Must be later than the end of the event."

    def test_additional_data_is_schema_checked(self, video_request):
        video_request.additional_data = {"randomKey": "randomValue"}

        with pytest.raises(ValidationError) as error:
            video_request.full_clean()

        assert (
            "Additional properties are not allowed ('randomKey' was unexpected)"
            in error.value.messages[0]
        )


class TestVideoAiredDates:
    def test_they_are_sorted_newest_first_on_save(self, video):
        video.additional_data["aired"] = [
            "2020-01-12",
            "2019-11-25",
            "2020-10-25",
            "2018-05-19",
            "2020-07-14",
        ]
        video.save()

        assert video.additional_data["aired"] == [
            "2020-10-25",
            "2020-07-14",
            "2020-01-12",
            "2019-11-25",
            "2018-05-19",
        ]


class TestTodoValidation:
    @pytest.mark.parametrize("with_video", [True, False])
    def test_a_todo_of_the_request_is_valid(self, video, video_request, with_video):
        todo = baker.make(
            "video_requests.Todo",
            request=video_request,
            video=video if with_video else None,
        )

        todo.full_clean()  # Should not raise

    def test_the_video_must_belong_to_the_request(self, video_request):
        todo = baker.make(
            "video_requests.Todo",
            request=video_request,
            video=baker.make("video_requests.Video"),
        )

        with pytest.raises(ValidationError) as error:
            todo.full_clean()

        assert error.value.message_dict == {
            "video": ["The video must belong to this request."]
        }


class TestVideoValidation:
    def test_a_freshly_built_video_is_valid(self, video):
        video.refresh_from_db()
        video.full_clean()  # Should not raise

    def test_additional_data_is_schema_checked(self, video):
        video.additional_data = {"randomKey": "randomValue"}

        with pytest.raises(ValidationError) as error:
            video.full_clean()

        assert (
            "Additional properties are not allowed ('randomKey' was unexpected)"
            in error.value.messages[0]
        )
