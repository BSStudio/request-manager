import re
from typing import Any

REDACTED = "[redacted]"

TRACES_SAMPLE_RATE = 0.5

# The free plan has one cron monitor. The SDK appends "$" and matches the beat
# schedule entry name, Celery's own celery.backend_cleanup included.
EXCLUDED_BEAT_TASKS = [r"^(?!sync_bss_users$).*$"]

# The email and phone patterns match backstage's lib/observability/scrub.ts.
_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    re.compile(
        r"(?:\+|00)\d[\d\s\-./()]{6,}\d"
        r"|\b06[\s\-./]?\d{1,2}[\s\-./]?\d{3}[\s\-./]?\d{3,4}\b"
    ),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    # Requires "::" or eight groups, so clock times like 12:30:05 survive.
    re.compile(
        r"(?<![\w:])(?:(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}"
        r"|(?:[0-9a-f]{1,4}:){0,6}[0-9a-f]{0,4}::(?:[0-9a-f]{1,4}:){0,6}[0-9a-f]{0,4})"
        r"(?![\w:])",
        re.IGNORECASE,
    ),
]


def redact(text: str) -> str:
    for pattern in _PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text


def traces_sampler(context: dict[str, Any]) -> float:
    # Also matches the token-protected health/<token>/ path.
    if context.get("wsgi_environ", {}).get("PATH_INFO", "").startswith("/health"):
        return 0
    if context.get("parent_sampled") is not None:
        return float(context["parent_sampled"])
    return TRACES_SAMPLE_RATE


def before_send_log(log: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any]:
    attributes = {
        key: redact(value) if isinstance(value, str) else value
        for key, value in log.get("attributes", {}).items()
    }
    return {**log, "body": redact(log["body"]), "attributes": attributes}
