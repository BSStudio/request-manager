import pytest

from common.sentry import before_send_log, redact


@pytest.mark.parametrize(
    "value",
    [
        "kovacs.anna@example.com",
        "+36 30 123 4567",
        "06 30 123 4567",
        "10.1.2.3",
        "2001:db8::1",
    ],
)
def test_redact_replaces_personal_data(value):
    assert redact(f"before {value} after") == "before [redacted] after"


def test_redact_keeps_username_id_and_path():
    text = "kovacs.anna 4242 /api/v1/requests/17 12:30:05"
    assert redact(text) == text


def test_redact_handles_postgres_unique_violation():
    message = "Key (email)=(kovacs.anna@example.com) already exists."
    assert redact(message) == "Key (email)=([redacted]) already exists."


def test_before_send_log_redacts_body_and_string_attributes():
    log = {
        "body": "Sent to kovacs.anna@example.com",
        "attributes": {
            "sentry.message.parameter.0": "kovacs.anna@example.com",
            "user.id": 7,
        },
    }

    result = before_send_log(log, {})

    assert result["body"] == "Sent to [redacted]"
    assert result["attributes"] == {
        "sentry.message.parameter.0": "[redacted]",
        "user.id": 7,
    }
