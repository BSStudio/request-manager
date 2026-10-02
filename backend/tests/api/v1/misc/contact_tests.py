import pytest
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from tests.api.helpers import do_login

pytestmark = [pytest.mark.django_db, pytest.mark.emails]


@pytest.fixture(autouse=True)
def celery_tasks_eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.fixture
def contact_data():
    return {
        "captcha": "randomCaptchaResponseToken",
        "email": "joe@example.com",
        "message": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer posuere tempus nibh et lobortis.",
        "name": "Joe Bloggs",
    }


@pytest.mark.parametrize(
    "user",
    ["admin_user", "staff_user", "basic_user", "service_account", None],
)
@pytest.mark.parametrize(
    "captcha_pass",
    [True, False],
)
def test_contact(
    api_client, captcha_pass, contact_data, mailoutbox, request, settings, user
):
    settings.TURNSTILE_TESTING_PASS = captcha_pass

    do_login(api_client, request, user)

    url = reverse("api:v1:misc:contact")
    response = api_client.post(url, contact_data)

    if captcha_pass:
        assert response.status_code == HTTP_201_CREATED

        assert len(mailoutbox) == 1
        assert contact_data["email"] in mailoutbox[0].to
        assert settings.DEFAULT_REPLY_EMAIL in mailoutbox[0].cc
        assert settings.DEFAULT_REPLY_EMAIL in mailoutbox[0].reply_to
        assert mailoutbox[0].subject == "Kapcsolatfelvétel | Budavári Schönherz Stúdió"

    else:
        assert response.status_code == HTTP_400_BAD_REQUEST

        assert response.data["captcha"][0] == ErrorDetail(
            string="Error verifying captcha, please try again.",
            code="captcha_invalid",
        )
