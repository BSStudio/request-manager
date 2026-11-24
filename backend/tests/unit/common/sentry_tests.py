import pytest
from sentry_sdk.utils import match_regex_list

from common.sentry import (
    EXCLUDED_BEAT_TASKS,
    TRACES_SAMPLE_RATE,
    before_send_log,
    redact,
    traces_sampler,
)


def request_context(path, **context):
    return {"wsgi_environ": {"PATH_INFO": path}, **context}


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


@pytest.mark.parametrize(
    "path", ["/health", "/health/secret-token/", "/livez", "/readyz"]
)
def test_traces_sampler_drops_health_checks_and_probes(path):
    assert traces_sampler(request_context(path)) == 0


def test_traces_sampler_samples_requests_and_tasks_at_the_budgeted_rate():
    assert TRACES_SAMPLE_RATE == 0.5
    assert traces_sampler(request_context("/api/v1/requests")) == 0.5
    assert traces_sampler({"celery_job": {"task": "core.tasks.x"}}) == 0.5


@pytest.mark.parametrize(("parent_sampled", "rate"), [(True, 1.0), (False, 0.0)])
def test_traces_sampler_follows_the_parent_decision(parent_sampled, rate):
    context = request_context("/api/v1/requests", parent_sampled=parent_sampled)
    assert traces_sampler(context) == rate


def test_only_sync_bss_users_is_monitored(settings):
    names = [*settings.CELERY_BEAT_SCHEDULE, "celery.backend_cleanup"]

    excluded = {name for name in names if match_regex_list(name, EXCLUDED_BEAT_TASKS)}

    assert excluded == set(names) - {"sync_bss_users"}
