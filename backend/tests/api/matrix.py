"""Permission matrices for the API tests.

Every endpoint answers the same five callers, so the table mapping caller to
expected status code is the most repeated shape in these tests. Named once here,
it becomes a single decorator at the call site::

    @staff_only(HTTP_200_OK)
    def test_list_comments(api_client, expected, request, user): ...

The generated parametrize ids stay ``<caller fixture>-<expected>``, exactly what a
hand-written table produces, so test ids do not move.
"""

import pytest
from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

#: Caller fixture names, in the order every table lists them. ``None`` is anonymous.
CALLERS = ("admin_user", "staff_user", "basic_user", "service_account", None)

FORBIDDEN = HTTP_403_FORBIDDEN
UNAUTHORIZED = HTTP_401_UNAUTHORIZED


def permissions(*, admin, staff, basic, service_account, anonymous=UNAUTHORIZED):
    """Parametrize ``user,expected`` with one expectation per caller.

    An expectation is a status code, or a ``{method: status code}`` mapping for a
    test that parametrizes the HTTP method too. A plain status code given
    alongside mappings is broadcast over the same methods, so only the roles that
    differ per method need spelling out.
    """
    outcomes = [admin, staff, basic, service_account, anonymous]
    methods = next((o for o in outcomes if isinstance(o, dict)), None)
    return pytest.mark.parametrize(
        "user,expected",
        [
            (caller, _broadcast(outcome, methods))
            for caller, outcome in zip(CALLERS, outcomes)
        ],
    )


def _broadcast(outcome, methods):
    if methods is None or isinstance(outcome, dict):
        return outcome
    return dict.fromkeys(methods, outcome)


def admin_only(allowed, *, denied=FORBIDDEN, anonymous=UNAUTHORIZED):
    """Only an administrator gets through."""
    return permissions(
        admin=allowed,
        staff=denied,
        basic=denied,
        service_account=denied,
        anonymous=anonymous,
    )


def staff_only(allowed, *, denied=FORBIDDEN, anonymous=UNAUTHORIZED):
    """Staff and administrators get through."""
    return permissions(
        admin=allowed,
        staff=allowed,
        basic=denied,
        service_account=denied,
        anonymous=anonymous,
    )


def any_user(allowed, *, denied=FORBIDDEN, anonymous=UNAUTHORIZED):
    """Everyone logged in gets through; a service account does not."""
    return permissions(
        admin=allowed,
        staff=allowed,
        basic=allowed,
        service_account=denied,
        anonymous=anonymous,
    )


def service_account_only(allowed, *, denied=FORBIDDEN, anonymous=UNAUTHORIZED):
    """Only a service account gets through."""
    return permissions(
        admin=denied,
        staff=denied,
        basic=denied,
        service_account=allowed,
        anonymous=anonymous,
    )
