from random import randint

import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from common.models import User
from video_requests.models import Comment, Request, Todo, Video


@pytest.fixture
def api_client():
    client = APIClient()
    return client


@pytest.fixture
def admin_user(settings):
    user = User.objects.create_user(
        email="admin@example.com",
        first_name="Admin",
        is_staff=True,
        last_name="Test",
        password="password",
        username="admin",
    )

    group = Group.objects.get_or_create(name=settings.ADMIN_GROUP)[0]
    user.groups.add(group)

    user.save()

    user.phone_number = "+36509999999"
    user.save()

    return user


@pytest.fixture
def staff_user():
    user = User.objects.create_user(
        email="staff@example.com",
        first_name="Staff",
        is_staff=True,
        last_name="Test",
        password="password",
        username="staff",
    )

    user.phone_number = "+36509999999"
    user.save()
    return user


@pytest.fixture
def basic_user():
    user = User.objects.create_user(
        email="basic@example.com",
        first_name="Basic",
        is_staff=False,
        last_name="Test",
        password="password",
        username="basic",
    )

    user.phone_number = "+36509999999"
    user.save()
    return user


@pytest.fixture
def service_account(settings):
    user = User.objects.create_user(
        email="service-account@example.com",
        first_name="Service",
        is_staff=False,
        last_name="Account",
        password="password",
        username="service-account",
    )

    grp = Group.objects.get_or_create(name=settings.SERVICE_ACCOUNTS_GROUP)[0]
    user.groups.add(grp)
    user.save()

    user.phone_number = "+36509999999"
    user.save()

    return user


@pytest.fixture
def not_existing_comment_id():
    while True:
        non_existing_id = randint(1000, 100000)
        if not Comment.objects.filter(pk=non_existing_id).exists():
            return non_existing_id


@pytest.fixture
def not_existing_todo_id():
    while True:
        non_existing_id = randint(1000, 100000)
        if not Todo.objects.filter(pk=non_existing_id).exists():
            return non_existing_id


@pytest.fixture
def not_existing_request_id():
    while True:
        non_existing_id = randint(1000, 100000)
        if not Request.objects.filter(pk=non_existing_id).exists():
            return non_existing_id


@pytest.fixture
def not_existing_user_id():
    while True:
        non_existing_id = randint(1000, 100000)
        if not User.objects.filter(pk=non_existing_id).exists():
            return non_existing_id


@pytest.fixture
def not_existing_video_id():
    while True:
        non_existing_id = randint(1000, 100000)
        if not Video.objects.filter(pk=non_existing_id).exists():
            return non_existing_id
