from model_bakery import baker
from rest_framework.authtoken.models import Token

from common.models import User


def authorize(client, user):
    """Authenticate as a service account, which uses a static token."""
    token = Token.objects.get_or_create(user=user)[0]
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")


def login(client, user):
    """Authenticate as a person, who has a session."""
    client.force_login(user)


def do_login(api_client, request, user):
    """Resolve a caller fixture name from a permission matrix and log them in.

    ``None`` means anonymous: nothing is sent, and the returned user is a
    throwaway so a test can still name a requester the caller does not own.
    """
    if user:
        user = request.getfixturevalue(user)
        if user.is_service_account:
            authorize(api_client, user)
        else:
            login(api_client, user)
    else:
        user = baker.make(User)
    return user


def get_response(api_client, method, url, data):
    if method == "GET":
        return api_client.get(url)
    elif method == "DELETE":
        return api_client.delete(url)
    elif method == "PATCH":
        return api_client.patch(url, data)
    elif method == "POST":
        return api_client.post(url, data)
    else:  # PUT
        return api_client.put(url, data)
