"""Only ``pytest_addoption`` lives here: pytest reads it from the rootdir conftest
alone. Fixtures live under tests/.
"""

import pytest

FILE_AND_MEMORY_BACKEND = "tests.helpers.email.CombinedEmailBackend"


def pytest_addoption(parser):
    parser.addoption(
        "--save-emails",
        action="store_true",
        default=False,
        help=(
            "Write every e-mail the `emails` tests render to logs/emails as well, "
            "for the CI job that publishes them as downloadable artifacts. Off by "
            "default so a normal run keeps the in-memory backend."
        ),
    )


@pytest.fixture(autouse=True)
def save_emails(request):
    """With ``--save-emails``, also write tests marked ``emails`` to disk."""
    if not request.node.get_closest_marker("emails"):
        return
    if not request.config.getoption("--save-emails"):
        return
    request.getfixturevalue("settings").EMAIL_BACKEND = FILE_AND_MEMORY_BACKEND
