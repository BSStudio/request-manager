from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import time_machine
from decouple import config
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.utils.timezone import localtime
from model_bakery import baker
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from common.models import User, get_system_user
from tests.helpers.test_utils import conditional_override_settings
from tests.helpers.users_test_utils import create_user
from tests.helpers.video_requests_test_utils import (
    create_crew,
    create_request,
    create_video,
)
from video_requests.emails import (
    email_crew_daily_reminder,
    email_crew_request_modified,
    email_production_manager_unfinished_requests,
    email_responsible_overdue_request,
    email_staff_weekly_tasks,
)
from video_requests.models import Request, Todo, Video

EMAIL_FILE = config("EMAIL_FILE", default=True, cast=bool)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@conditional_override_settings(
    EMAIL_BACKEND="tests.helpers.test_utils.CombinedEmailBackend", CONDITION=EMAIL_FILE
)
class EmailSendingTestCase(APITestCase):
    """
    IMPORTANT: You need to run "python manage.py collectstatic" before running this test case!
    """

    def authorize_user(self, user):
        token = AccessToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")

    def setUp(self):
        # Create normal user
        self.normal_user = create_user()

        # Create staff user
        self.staff_user = create_user(is_staff=True)

        # Create special users
        self.editor_in_chief = create_user(is_staff=True, groups=["Főszerkesztő"])
        self.production_manager = create_user(is_staff=True, groups=["Gyártásvezető"])
        self.pr_responsible = create_user(is_staff=True, groups=["PR felelős"])

    def test_new_request_confirmation_email_sent_to_logged_in_user(self):
        # Create a Request with logged in user
        self.authorize_user(self.normal_user)
        data = {
            "title": "Test Request",
            "start_datetime": localtime() + timedelta(minutes=10),
            "end_datetime": localtime() + timedelta(days=1),
            "place": "Test place",
            "type": "Test type",
        }
        url = reverse("api:v1:requests:request-list")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.normal_user.email, mail.outbox[0].to)
        self.assertIn(self.editor_in_chief.email, mail.outbox[0].bcc)
        self.assertIn(settings.DEFAULT_REPLY_EMAIL, mail.outbox[0].reply_to)
        self.assertEqual(
            mail.outbox[0].subject, f"{data['title']} | Forgatási felkérésedet fogadtuk"
        )

    def test_new_request_confirmation_email_sent_when_admin_or_staff_checks_send_notification(
        self,
    ):
        # Create a Request with a staff user
        self.authorize_user(self.staff_user)
        data = {
            "title": "Test Request",
            "start_datetime": localtime() + timedelta(minutes=10),
            "end_datetime": localtime() + timedelta(days=1),
            "place": "Test place",
            "type": "Test type",
            "send_notification": True,
        }
        url = reverse("api:v1:admin:requests:request-list")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.staff_user.email, mail.outbox[0].to)
        self.assertIn(self.editor_in_chief.email, mail.outbox[0].bcc)
        self.assertIn(settings.DEFAULT_REPLY_EMAIL, mail.outbox[0].reply_to)
        self.assertEqual(
            mail.outbox[0].subject, f"{data['title']} | Forgatási felkérésedet fogadtuk"
        )

    @override_settings(TURNSTILE_TESTING_PASS=True)
    def test_new_request_confirmation_email_sent_to_anonymous(self):
        # Create a Request without login
        data = {
            "title": "Test Request",
            "start_datetime": localtime() + timedelta(minutes=10),
            "end_datetime": localtime() + timedelta(days=1),
            "place": "Test place",
            "type": "Test type",
            "requester_first_name": "Test",
            "requester_last_name": "User",
            "requester_email": "test.user@example.com",
            "requester_mobile": "+36509999999",
            "comment": "Additional information",
            "captcha": "randomCaptchaResponseToken",
        }
        url = reverse("api:v1:requests:request-list")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(data["requester_email"], mail.outbox[0].to)
        self.assertIn(self.editor_in_chief.email, mail.outbox[0].bcc)
        self.assertIn(settings.DEFAULT_REPLY_EMAIL, mail.outbox[0].reply_to)
        self.assertEqual(
            mail.outbox[0].subject, f"{data['title']} | Forgatási felkérésedet fogadtuk"
        )

    def test_video_published_email_sent_to_user_and_todo_created(self):
        # Setup data - Create a Request with status 4, and a video
        request = create_request(
            100,
            self.normal_user,
            Request.Statuses.UPLOADED,
            "2020-11-16T04:16:13+0100",
            "2020-11-17T04:16:13+0100",
        )
        request.additional_data = {"accepted": True, "recording": {"path": "test/path"}}
        request.save()
        video = create_video(300, request, Video.Statuses.PENDING)

        # Video data to be patched
        data = {
            "editor": self.staff_user.id,
            "additional_data": {
                "editing_done": True,
                "coding": {"website": True},
                "publishing": {"website": "https://example.com"},
            },
        }

        # Authorized staff user and update video data
        self.authorize_user(self.staff_user)
        url = reverse(
            "api:v1:admin:requests:request:video-detail",
            kwargs={"request_pk": request.id, "pk": video.id},
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Video.Statuses.PUBLISHED)

        todos = Todo.objects.filter(video=video)
        self.assertEqual(len(todos), 1)
        self.assertTrue(todos[0].assignees.contains(self.pr_responsible))
        self.assertEqual(todos[0].creator, get_system_user())
        self.assertEqual(todos[0].description, "Megosztás közösségi platformokon")

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(self.pr_responsible.email, mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].subject, "Feladatot rendeltek hozzád")
        self.assertIn(self.normal_user.email, mail.outbox[1].to)
        self.assertIn(settings.DEFAULT_REPLY_EMAIL, mail.outbox[1].reply_to)
        self.assertEqual(
            mail.outbox[1].subject, f"{video.request.title} | Új videót publikáltunk"
        )

        # Revert the published status
        data = {
            "additional_data": {
                "publishing": {"website": ""},
            },
        }
        url = reverse(
            "api:v1:admin:requests:request:video-detail",
            kwargs={"request_pk": request.id, "pk": video.id},
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Video.Statuses.CODED)

        # Publish again
        data = {
            "additional_data": {
                "publishing": {"website": "https://example123.com"},
            },
        }
        url = reverse(
            "api:v1:admin:requests:request:video-detail",
            kwargs={"request_pk": request.id, "pk": video.id},
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Video.Statuses.PUBLISHED)

        # No new to-do was created
        todos = Todo.objects.filter(video=video)
        self.assertEqual(len(todos), 1)

        # No new e-mail should be sent
        self.assertEqual(len(mail.outbox), 2)

    def test_video_published_email_not_sent_to_staff_but_todo_created(self):
        # Setup data - Create a Request with status 4, and a video
        request = create_request(
            100,
            self.staff_user,
            Request.Statuses.UPLOADED,
            "2020-11-16T04:16:13+0100",
            "2020-11-17T04:16:13+0100",
        )
        request.additional_data = {"accepted": True, "recording": {"path": "test/path"}}
        request.save()
        video = create_video(300, request, Video.Statuses.PENDING)

        # Video data to be patched
        data = {
            "editor": self.staff_user.id,
            "additional_data": {
                "editing_done": True,
                "coding": {"website": True},
                "publishing": {"website": "https://example.com"},
            },
        }

        # Authorized staff user and update video data
        self.authorize_user(self.staff_user)
        url = reverse(
            "api:v1:admin:requests:request:video-detail",
            kwargs={"request_pk": request.id, "pk": video.id},
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Video.Statuses.PUBLISHED)

        todos = Todo.objects.filter(video=video)
        self.assertEqual(len(todos), 1)
        self.assertTrue(todos[0].assignees.contains(self.pr_responsible))
        self.assertEqual(todos[0].creator, get_system_user())
        self.assertEqual(todos[0].description, "Megosztás közösségi platformokon")

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.pr_responsible.email, mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].subject, "Feladatot rendeltek hozzád")

        # Revert the published status
        data = {
            "additional_data": {
                "publishing": {"website": ""},
            },
        }
        url = reverse(
            "api:v1:admin:requests:request:video-detail",
            kwargs={"request_pk": request.id, "pk": video.id},
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Video.Statuses.CODED)

        # Publish again
        data = {
            "additional_data": {
                "publishing": {"website": "https://example123.com"},
            },
        }
        url = reverse(
            "api:v1:admin:requests:request:video-detail",
            kwargs={"request_pk": request.id, "pk": video.id},
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Video.Statuses.PUBLISHED)

        # No new to-do was created
        todos = Todo.objects.filter(video=video)
        self.assertEqual(len(todos), 1)

        # No new e-mail should be sent
        self.assertEqual(len(mail.outbox), 1)

    def test_todo_email_sent_new_todo(self):
        video_request = baker.make("video_requests.Request")
        video = baker.make("video_requests.Video", request=video_request)
        users = baker.make(User, is_staff=True, _fill_optional=True, _quantity=5)

        self.authorize_user(self.staff_user)

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
            response = self.client.post(
                url,
                {
                    "assignees": [user.id for user in users],
                    "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                    "status": Todo.Statuses.CLOSED,
                },
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(len(mail.outbox), 2)
        self.assertListEqual([user.email for user in users], mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].subject, "Feladatot rendeltek hozzád")
        self.assertListEqual([user.email for user in users], mail.outbox[1].to)
        self.assertEqual(mail.outbox[1].subject, "Feladatot rendeltek hozzád")

    def test_todo_email_sent_new_assignee(self):
        video_request = baker.make("video_requests.Request")
        users_existing = baker.make(
            User, is_staff=True, _fill_optional=True, _quantity=2
        )
        users_new = baker.make(User, is_staff=True, _fill_optional=True, _quantity=3)
        todo = baker.make(
            "video_requests.Todo", assignees=users_existing, request=video_request
        )

        self.authorize_user(self.staff_user)

        url = reverse(
            "api:v1:admin:todos:todo-detail",
            kwargs={"pk": todo.id},
        )

        response = self.client.patch(
            url, {"assignees": [user.id for user in users_new + users_existing]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Only the new assignees should get an e-mail
        self.assertEqual(len(mail.outbox), 2)
        self.assertListEqual([user.email for user in users_new], mail.outbox[1].to)
        self.assertEqual(mail.outbox[1].subject, "Feladatot rendeltek hozzád")

    def test_todo_email_not_sent_when_removing_assignee(self):
        video_request = baker.make("video_requests.Request")
        users_existing = baker.make(
            User, is_staff=True, _fill_optional=True, _quantity=3
        )
        todo = baker.make(
            "video_requests.Todo", assignees=users_existing, request=video_request
        )

        self.authorize_user(self.staff_user)

        url = reverse(
            "api:v1:admin:todos:todo-detail",
            kwargs={"pk": todo.id},
        )

        response = self.client.patch(
            url, {"assignees": [user.id for user in users_existing[0:1]]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Creating the to-do will send one e-mail automatically
        self.assertEqual(len(mail.outbox), 1)

    def test_todo_email_sent_only_to_staff(self):
        video_request = baker.make("video_requests.Request")
        users_existing = baker.make(
            User, is_staff=False, _fill_optional=True, _quantity=2
        )
        users_new = baker.make(User, is_staff=False, _fill_optional=True, _quantity=3)
        todo = baker.make(
            "video_requests.Todo", assignees=users_existing, request=video_request
        )

        self.authorize_user(self.staff_user)

        url = reverse(
            "api:v1:admin:todos:todo-detail",
            kwargs={"pk": todo.id},
        )

        response = self.client.patch(
            url, {"assignees": [user.id for user in users_new + users_existing]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 0)

    def test_new_comment_email_sent_to_user_and_crew_admin_endpoint_non_internal(self):
        # Setup data - Create a Request, add Crew members and Responsible
        crew_member1 = create_user(is_staff=True)
        crew_member2 = create_user(is_staff=True)
        responsible = create_user(is_staff=True)
        request = create_request(100, self.normal_user, responsible=responsible)
        create_crew(200, request, crew_member1, "Cameraman")
        create_crew(201, request, crew_member2, "Reporter")

        # New comment data
        data = {
            "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut ut ex erat. Nunc rutrum ac odio nec accumsan. Integer tristique nibh mollis nunc rhoncus, at dictum dui pellentesque. Integer ut tortor libero. Maecenas nec sollicitudin neque, a laoreet quam. Duis eu enim enim. Vestibulum porta commodo dictum.\nSuspendisse condimentum, nisl ut elementum mattis, felis mauris dictum enim, at viverra elit felis eget elit. Nam finibus quis neque id varius. Aenean vel metus et ipsum feugiat consectetur nec at elit. In malesuada scelerisque quam ac blandit. Donec venenatis aliquam ex ac dignissim. Pellentesque eleifend tortor a purus egestas, eget pretium mi egestas. Sed non neque maximus, iaculis ex at, egestas augue. Maecenas non enim eu libero facilisis cursus at sed quam. Duis at tortor sapien. Duis congue turpis libero, ut dapibus eros efficitur vel. Curabitur aliquam eros eget gravida congue. Donec et libero egestas, hendrerit elit sed, fermentum sapien. Nunc placerat tempor metus vel efficitur. In eget tortor id est mattis blandit vitae vel mi. Integer aliquet at odio ac dictum.\nUt eros nibh, tincidunt sit amet felis vitae, vehicula posuere diam. Nunc a aliquam enim, eget scelerisque lectus. Maecenas et risus in leo luctus sodales eu venenatis mauris. Vivamus quis metus finibus, vehicula tellus nec, placerat tortor. Quisque vel felis auctor, scelerisque massa sit amet, gravida ex. Phasellus orci dolor, faucibus placerat purus nec, iaculis faucibus tortor. Aenean fringilla justo a metus placerat, ut volutpat quam scelerisque. Ut laoreet ullamcorper quam. Aenean sed sodales sem. Nulla dolor tortor, sagittis quis dui non, dapibus hendrerit ligula. Fusce consectetur sapien arcu. Nunc accumsan leo et turpis convallis sagittis. Sed tincidunt nunc ut vehicula cursus. Sed facilisis tortor ac ex dapibus interdum.",
            "internal": False,
        }

        # Authorized staff user and create new comment
        self.authorize_user(self.staff_user)
        url = reverse(
            "api:v1:admin:requests:request:comment-list",
            kwargs={"request_pk": request.id},
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 2)
        # User e-mail
        self.assertIn(self.normal_user.email, mail.outbox[0].to)
        self.assertIn(settings.DEFAULT_REPLY_EMAIL, mail.outbox[0].reply_to)
        self.assertEqual(
            mail.outbox[0].subject, f"{request.title} | Hozzászólás érkezett"
        )
        # Crew e-mail
        self.assertIn(crew_member1.email, mail.outbox[1].to)
        self.assertIn(crew_member2.email, mail.outbox[1].to)
        self.assertIn(responsible.email, mail.outbox[1].cc)
        self.assertIn(self.editor_in_chief.email, mail.outbox[1].cc)
        self.assertEqual(
            mail.outbox[1].subject, f"{request.title} | Hozzászólás érkezett"
        )
        # Both templates show the commenter's avatar
        avatar_url = self.staff_user.avatar_url
        self.assertIn(avatar_url, mail.outbox[0].alternatives[0].content)
        self.assertIn(avatar_url, mail.outbox[1].alternatives[0].content)

    def test_new_comment_email_sent_to_crew_admin_endpoint_internal(self):
        # Setup data - Create a Request, add Crew members and Responsible
        crew_member1 = create_user(is_staff=True)
        crew_member2 = create_user(is_staff=True)
        responsible = create_user(is_staff=True)
        request = create_request(100, self.normal_user, responsible=responsible)
        create_crew(200, request, crew_member1, "Cameraman")
        create_crew(201, request, crew_member2, "Reporter")

        # New comment data
        data = {"text": "New comment", "internal": True}

        # Authorized staff user and create new comment
        self.authorize_user(self.staff_user)
        url = reverse(
            "api:v1:admin:requests:request:comment-list",
            kwargs={"request_pk": request.id},
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(self.normal_user.email, mail.outbox[0].to)
        self.assertNotIn(self.normal_user.email, mail.outbox[0].cc)
        self.assertNotIn(self.normal_user.email, mail.outbox[0].bcc)
        self.assertIn(crew_member1.email, mail.outbox[0].to)
        self.assertIn(crew_member2.email, mail.outbox[0].to)
        self.assertIn(responsible.email, mail.outbox[0].cc)
        self.assertIn(self.editor_in_chief.email, mail.outbox[0].cc)
        self.assertEqual(
            mail.outbox[0].subject, f"{request.title} | Hozzászólás érkezett"
        )

    def test_new_comment_email_not_sent_to_banned_user_admin_endpoint(self):
        # Setup data - Create a Request, add Crew members and Responsible
        banned_user = create_user(banned=True)
        request = create_request(100, banned_user)

        # New comment data
        data = {"text": "New comment", "internal": False}

        # Authorized staff user and create new comment
        self.authorize_user(self.staff_user)
        url = reverse(
            "api:v1:admin:requests:request:comment-list",
            kwargs={"request_pk": request.id},
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(banned_user.email, mail.outbox[0].to)
        self.assertNotIn(banned_user.email, mail.outbox[0].cc)
        self.assertNotIn(banned_user.email, mail.outbox[0].bcc)

    def test_new_comment_email_sent_to_crew_default_endpoint(self):
        # Setup data - Create a Request, add Crew members and Responsible
        crew_member1 = create_user(is_staff=True)
        crew_member2 = create_user(is_staff=True)
        responsible = create_user(is_staff=True)
        request = create_request(100, self.normal_user, responsible=responsible)
        create_crew(200, request, crew_member1, "Cameraman")
        create_crew(201, request, crew_member2, "Reporter")

        # New comment data
        data = {
            "text": "New comment",
        }

        # Authorized staff user and create new comment
        self.authorize_user(self.normal_user)
        url = reverse(
            "api:v1:requests:request:comment-list",
            kwargs={"request_pk": request.id},
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(self.normal_user.email, mail.outbox[0].to)
        self.assertNotIn(self.normal_user.email, mail.outbox[0].cc)
        self.assertNotIn(self.normal_user.email, mail.outbox[0].bcc)
        self.assertIn(crew_member1.email, mail.outbox[0].to)
        self.assertIn(crew_member2.email, mail.outbox[0].to)
        self.assertIn(responsible.email, mail.outbox[0].cc)
        self.assertIn(self.editor_in_chief.email, mail.outbox[0].cc)
        self.assertEqual(
            mail.outbox[0].subject, f"{request.title} | Hozzászólás érkezett"
        )

    def test_request_modified_email_sent_when_send_notification_checked(self):
        # Setup data - Create a Request, add Crew members and Responsible
        crew_member1 = create_user(is_staff=True)
        crew_member2 = create_user(is_staff=True)
        responsible = create_user(is_staff=True)
        request = create_request(100, self.normal_user, responsible=responsible)
        create_crew(200, request, crew_member1, "Cameraman")
        create_crew(201, request, crew_member2, "Reporter")

        # Modify request and send notification
        self.authorize_user(self.staff_user)
        data = {
            "title": "Test Request Modified",
            "start_datetime": localtime() + timedelta(minutes=10),
            "end_datetime": localtime() + timedelta(days=3),
            "place": "New place",
            "type": "New type",
            "send_notification": True,
        }
        url = reverse("api:v1:admin:requests:request-detail", kwargs={"pk": request.id})
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(crew_member1.email, mail.outbox[0].to)
        self.assertIn(crew_member2.email, mail.outbox[0].to)
        self.assertIn(responsible.email, mail.outbox[0].cc)
        self.assertIn(self.editor_in_chief.email, mail.outbox[0].cc)
        self.assertEqual(
            mail.outbox[0].subject, f"{data['title']} | Felkérés módosítva"
        )

    @patch(
        "video_requests.emails.email_crew_request_modified.delay",
        wraps=email_crew_request_modified,
    )
    def test_request_modified_email_sending_called_with_right_values(
        self, mock_email_crew_request_modified
    ):
        request = create_request(100, self.normal_user)
        url = reverse("api:v1:admin:requests:request-detail", kwargs={"pk": request.id})

        self.authorize_user(self.staff_user)

        # Change deadline - Should not send e-mail
        data = {
            "deadline": (request.end_datetime + timedelta(weeks=1)).date(),
            "send_notification": True,
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_email_crew_request_modified.assert_not_called()

        # Change title - Should work
        data = {"title": "TC1", "send_notification": True}

        changed_values = [
            {"name": "Esemény neve", "next": data["title"], "previous": request.title}
        ]

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_email_crew_request_modified.assert_called_once()

        self.assertEqual(mock_email_crew_request_modified.call_args.args[0], request.id)
        self.assertEqual(
            mock_email_crew_request_modified.call_args.args[1],
            self.staff_user.get_full_name_eastern_order(),
        )
        self.assertEqual(
            mock_email_crew_request_modified.call_args.args[3], changed_values
        )

        mock_email_crew_request_modified.reset_mock()

        # Change title and deadline - Only title should be included
        data = {
            "title": "TC2",
            "deadline": (request.end_datetime + timedelta(weeks=2)).date(),
            "send_notification": True,
        }

        changed_values = [
            {
                "name": "Esemény neve",
                "next": data["title"],
                "previous": response.data["title"],
            }
        ]

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_email_crew_request_modified.assert_called_once()

        self.assertEqual(mock_email_crew_request_modified.call_args.args[0], request.id)
        self.assertEqual(
            mock_email_crew_request_modified.call_args.args[1],
            self.staff_user.get_full_name_eastern_order(),
        )
        self.assertEqual(
            mock_email_crew_request_modified.call_args.args[3], changed_values
        )

        mock_email_crew_request_modified.reset_mock()

        # Change multiple values
        data = {
            "title": "TC3",
            "start_datetime": request.start_datetime + timedelta(minutes=5),
            "end_datetime": request.end_datetime + timedelta(minutes=5),
            "place": "TC3 - Place",
            "type": "TC3 - Type",
            "send_notification": True,
        }

        changed_values = [
            {
                "name": "Esemény neve",
                "next": data["title"],
                "previous": response.data["title"],
            },
            {
                "name": "Esemény kezdésének ideje",
                "next": data["start_datetime"],
                "previous": request.start_datetime,
            },
            {
                "name": "Esemény várható befejezése",
                "next": data["end_datetime"],
                "previous": request.end_datetime,
            },
            {"name": "Helyszín", "next": data["place"], "previous": request.place},
            {"name": "Videó típusa", "next": data["type"], "previous": request.type},
        ]

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_email_crew_request_modified.assert_called_once()

        self.assertEqual(mock_email_crew_request_modified.call_args.args[0], request.id)
        self.assertEqual(
            mock_email_crew_request_modified.call_args.args[1],
            self.staff_user.get_full_name_eastern_order(),
        )
        self.assertEqual(
            mock_email_crew_request_modified.call_args.args[3], changed_values
        )

        mock_email_crew_request_modified.reset_mock()

    """
    SCHEDULED TASKS
    Management commands will be called manually for the tests.
    In production use it is done by Celery Beat
    """

    @patch(
        "video_requests.emails.email_staff_weekly_tasks", wraps=email_staff_weekly_tasks
    )
    def test_weekly_staff_email_sending(self, mock_email_staff_weekly_tasks):
        with time_machine.travel("2020-11-19 10:20:30 +0100") as traveller:
            # Create test Requests - Recording
            # Should be included
            rec1 = create_request(
                100, self.normal_user, start="2020-11-16T04:16:13+0100"
            )
            rec2 = create_request(
                101,
                self.normal_user,
                Request.Statuses.ACCEPTED,
                start="2020-11-21T21:41:57+0100",
            )
            # Add some crew members
            create_crew(120, rec1, self.staff_user, "Cameraman")
            create_crew(121, rec1, self.normal_user, "Reporter")
            # Should not be included
            rec3 = create_request(
                102, self.normal_user, start="2020-11-15T10:01:24+0100"
            )  # previous week
            rec4 = create_request(
                103, self.normal_user, start="2020-11-24T17:22:05+0100"
            )  # next week
            rec5 = create_request(
                104,
                self.normal_user,
                Request.Statuses.EDITED,
                start="2020-11-20T14:55:45+0100",
            )  # this week but wrong status

            # Create test Requests - Editing
            # Should be included
            edit1 = create_request(110, self.normal_user, Request.Statuses.RECORDED)
            edit2 = create_request(111, self.normal_user, Request.Statuses.UPLOADED)
            edit_vid21 = create_video(211, edit2, Video.Statuses.PENDING)
            edit_vid22 = create_video(
                212, edit2, Video.Statuses.IN_PROGRESS, self.staff_user
            )
            # Should not be included
            edit3 = create_request(
                112, self.normal_user, Request.Statuses.EDITED
            )  # later status
            edit4 = create_request(
                113, self.normal_user, Request.Statuses.RECORDED
            )  # good status but wrong status video
            edit_vid41 = create_video(213, edit4, Video.Statuses.EDITED)
            edit5 = create_request(
                114, self.normal_user, Request.Statuses.EDITED
            )  # wrong status but good status video
            edit_vid51 = create_video(214, edit5, Video.Statuses.PENDING)

            """
            Case 1: Successful e-mail sending
            """
            # Call management command
            with StringIO() as out:
                call_command("email_weekly_tasks", stdout=out)
                self.assertEqual(
                    out.getvalue(), "Weekly tasks email was sent successfully.\n"
                )

            # Check if fuction was called with correct parameters
            mock_email_staff_weekly_tasks.assert_called_once()

            self.assertEqual(len(mock_email_staff_weekly_tasks.call_args.args[0]), 2)
            self.assertIn(rec1, mock_email_staff_weekly_tasks.call_args.args[0])
            self.assertIn(rec2, mock_email_staff_weekly_tasks.call_args.args[0])
            self.assertNotIn(rec3, mock_email_staff_weekly_tasks.call_args.args[0])
            self.assertNotIn(rec4, mock_email_staff_weekly_tasks.call_args.args[0])
            self.assertNotIn(rec5, mock_email_staff_weekly_tasks.call_args.args[0])

            self.assertEqual(len(mock_email_staff_weekly_tasks.call_args.args[1]), 1)
            self.assertIn(edit1, mock_email_staff_weekly_tasks.call_args.args[1])
            self.assertNotIn(edit2, mock_email_staff_weekly_tasks.call_args.args[1])
            self.assertNotIn(edit3, mock_email_staff_weekly_tasks.call_args.args[1])
            self.assertNotIn(edit4, mock_email_staff_weekly_tasks.call_args.args[1])
            self.assertNotIn(edit5, mock_email_staff_weekly_tasks.call_args.args[1])

            self.assertEqual(len(mock_email_staff_weekly_tasks.call_args.args[2]), 2)
            self.assertIn(edit_vid21, mock_email_staff_weekly_tasks.call_args.args[2])
            self.assertIn(edit_vid22, mock_email_staff_weekly_tasks.call_args.args[2])
            self.assertNotIn(
                edit_vid41, mock_email_staff_weekly_tasks.call_args.args[2]
            )
            self.assertNotIn(
                edit_vid51, mock_email_staff_weekly_tasks.call_args.args[2]
            )

            # Check if e-mail was sent to the right people
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(settings.WEEKLY_TASK_EMAIL, mail.outbox[0].to)
            self.assertEqual(
                mail.outbox[0].subject, "Eheti forgatások és vágandó anyagok"
            )

            """
            Case 2: No Request for the week.
            """
            # Change time to next month
            traveller.move_to("2020-12-21 10:20:30 +0100")

            # Change editing objects
            edit1.status = Request.Statuses.EDITED
            edit1.save()
            edit2.status = Request.Statuses.ARCHIVED
            edit2.save()

            # Call management command
            with StringIO() as out:
                call_command("email_weekly_tasks", stdout=out)
                self.assertEqual(out.getvalue(), "No tasks for this week.\n")

    @patch(
        "video_requests.emails.email_crew_daily_reminder",
        wraps=email_crew_daily_reminder,
    )
    def test_daily_reminder_email_sent_to_crew(self, mock_email_crew_daily_reminder):
        with time_machine.travel("2020-11-19 10:20:30 +0100") as traveller:
            # Create test Requests
            with_crew = create_request(
                100, self.normal_user, start="2020-11-19T18:00:00+0100"
            )
            without_crew = create_request(
                101, self.normal_user, start="2020-11-19T20:00:00+0100"
            )
            crew1 = create_crew(201, with_crew, self.staff_user, "Cameraman")
            crew2 = create_crew(202, with_crew, self.editor_in_chief, "Reporter")

            """
            Case 1: Successful e-mail sending
            """
            # Call management command
            with StringIO() as out:
                call_command("email_daily_reminders", stdout=out)
                self.assertEqual(
                    out.getvalue(),
                    "1 reminders were sent to crew members. There are 2 request(s) today.\n",
                )

            # Check if function was called with correct parameters
            mock_email_crew_daily_reminder.assert_called_once()

            self.assertEqual(
                with_crew, mock_email_crew_daily_reminder.call_args.args[0]
            )
            self.assertNotEqual(
                without_crew, mock_email_crew_daily_reminder.call_args.args[0]
            )

            self.assertIn(crew1, mock_email_crew_daily_reminder.call_args.args[1])
            self.assertIn(crew2, mock_email_crew_daily_reminder.call_args.args[1])

            # Check if e-mail was sent to the right people
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(crew1.member.email, mail.outbox[0].to)
            self.assertIn(crew2.member.email, mail.outbox[0].to)
            self.assertEqual(
                mail.outbox[0].subject,
                f"Emlékeztető | {with_crew.title} | Mai forgatás",
            )

            """
            Case 2: No Request for today
            """
            # Change time to next day
            traveller.move_to("2020-11-20 10:20:30 +0100")

            # Call management command
            with StringIO() as out:
                call_command("email_daily_reminders", stdout=out)
                self.assertEqual(out.getvalue(), "No reminders for today.\n")

    @patch(
        "video_requests.emails.email_production_manager_unfinished_requests",
        wraps=email_production_manager_unfinished_requests,
    )
    def test_unfinished_requests_email_sent_to_production_manager(
        self, mock_email_production_manager_unfinished_requests
    ):
        # Setup test Requests
        not_incl_1 = create_request(100, self.normal_user, Request.Statuses.ACCEPTED)
        not_incl_2 = create_request(101, self.normal_user, Request.Statuses.UPLOADED)
        not_incl_3 = create_request(102, self.normal_user, Request.Statuses.DONE)
        incl_1 = create_request(103, self.normal_user, Request.Statuses.EDITED)
        incl_2 = create_request(104, self.normal_user, Request.Statuses.ARCHIVED)

        """
        Case 1: Some unfinished Requests
        """

        # Call management command
        with StringIO() as out:
            call_command("email_unfinished_requests", stdout=out)
            self.assertEqual(
                out.getvalue(), "Unfinished requests email was sent successfully.\n"
            )

        # Check if function was called with correct parameters
        mock_email_production_manager_unfinished_requests.assert_called_once()

        self.assertEqual(
            len(mock_email_production_manager_unfinished_requests.call_args.args[0]), 2
        )
        self.assertIn(
            incl_1, mock_email_production_manager_unfinished_requests.call_args.args[0]
        )
        self.assertIn(
            incl_2, mock_email_production_manager_unfinished_requests.call_args.args[0]
        )
        self.assertNotIn(
            not_incl_1,
            mock_email_production_manager_unfinished_requests.call_args.args[0],
        )
        self.assertNotIn(
            not_incl_2,
            mock_email_production_manager_unfinished_requests.call_args.args[0],
        )
        self.assertNotIn(
            not_incl_3,
            mock_email_production_manager_unfinished_requests.call_args.args[0],
        )

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.production_manager.email, mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].subject, "Lezáratlan anyagok")

        """
        Case 2: No unfinished Request
        """
        # Delete the included Requests
        incl_1.delete()
        incl_2.delete()

        # Reset mock
        mock_email_production_manager_unfinished_requests.reset_mock()

        # Call management command
        with StringIO() as out:
            call_command("email_unfinished_requests", stdout=out)
            self.assertEqual(out.getvalue(), "All requests are finished.\n")

        # Check if function was called with correct parameters
        mock_email_production_manager_unfinished_requests.assert_not_called()

    @time_machine.travel("2020-11-19 10:20:30 +0100")
    @patch(
        "video_requests.emails.email_responsible_overdue_request",
        wraps=email_responsible_overdue_request,
    )
    def test_overdue_requests_email_sent_to_editor_in_chief_and_production_manager(
        self, mock_email_responsible_overdue_request
    ):
        # Setup test objects
        new_staff_member = create_user(is_staff=True)
        overdue1 = create_request(
            100,
            self.normal_user,
            start="2020-10-05T18:00:00+0100",
            responsible=self.staff_user,
        )
        overdue2 = create_request(
            101,
            self.normal_user,
            Request.Statuses.UPLOADED,
            start="2020-09-29T15:30:00+0100",
            responsible=new_staff_member,
        )
        create_request(
            102,
            self.normal_user,
            Request.Statuses.ARCHIVED,
            start="2020-09-29T15:30:00+0100",
        )
        create_request(
            103,
            self.normal_user,
            Request.Statuses.UPLOADED,
            start="2020-11-05T21:00:00+0100",
        )

        """
        Case 1: Some overdue Requests
        """
        # Call management command
        with StringIO() as out:
            call_command("email_overdue_requests", stdout=out)
            self.assertEqual(
                out.getvalue(),
                f"Overdue request email was sent successfully. ({overdue1.title})\nOverdue request email was sent successfully. ({overdue2.title})\n",
            )

        # Check if function was called with correct parameters
        mock_email_responsible_overdue_request.assert_called()
        self.assertEqual(mock_email_responsible_overdue_request.call_count, 2)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(self.staff_user.email, mail.outbox[0].to)
        self.assertIn(self.production_manager.email, mail.outbox[0].cc)
        self.assertIn(self.editor_in_chief.email, mail.outbox[0].cc)
        self.assertEqual(
            mail.outbox[0].subject, f"Lejárt határidejű felkérés - {overdue1.title}"
        )

        self.assertIn(new_staff_member.email, mail.outbox[1].to)
        self.assertIn(self.production_manager.email, mail.outbox[1].cc)
        self.assertIn(self.editor_in_chief.email, mail.outbox[1].cc)
        self.assertEqual(
            mail.outbox[1].subject, f"Lejárt határidejű felkérés - {overdue2.title}"
        )

        """
        Case 2: No overdue Request until today
        """
        # Change the previous Request statuses
        overdue1.status = Request.Statuses.EDITED
        overdue1.save()
        overdue2.status = Request.Statuses.DONE
        overdue2.save()

        # Reset mock
        mock_email_responsible_overdue_request.reset_mock()

        # Call management command
        with StringIO() as out:
            call_command("email_overdue_requests", stdout=out)
            self.assertEqual(
                out.getvalue(),
                "No overdue request was found.\n",
            )

        # Check if function was called with correct parameters
        mock_email_responsible_overdue_request.assert_not_called()

    @override_settings(TURNSTILE_TESTING_PASS=True)
    def test_contact_message_email_sent(self):
        data = {
            "name": "Joe Bloggs",
            "email": "joe@example.com",
            "message": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer posuere tempus nibh et lobortis.",
            "captcha": "randomCaptchaResponseToken",
        }
        url = reverse("api:v1:misc:contact")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if e-mail was sent to the right people
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(data["email"], mail.outbox[0].to)
        self.assertIn(settings.DEFAULT_REPLY_EMAIL, mail.outbox[0].cc)
        self.assertIn(settings.DEFAULT_REPLY_EMAIL, mail.outbox[0].reply_to)
        self.assertEqual(
            mail.outbox[0].subject, "Kapcsolatfelvétel | Budavári Schönherz Stúdió"
        )
