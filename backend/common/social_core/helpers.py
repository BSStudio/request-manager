import logging

from social_core.exceptions import AuthException, SocialAuthBaseException
from social_core.utils import get_strategy
from social_django.utils import STORAGE, psa

logger = logging.getLogger(__name__)


def load_strategy(request=None):
    return get_strategy("common.social_core.strategy.DRFStrategy", STORAGE, request)


@psa("/redirect", load_strategy=load_strategy)
def decorate_request(request, backend):
    pass


def handle_exception(e):
    message = None
    if not isinstance(e, AuthException):
        log_exception(e)
    if hasattr(e, "response"):
        try:
            message = e.response.json()["error"]
            if isinstance(message, dict) and "message" in message:
                message = message["message"]
            elif isinstance(message, list) and len(message):
                message = message[0]
        except (KeyError, TypeError):
            logger.debug(
                "Could not parse error message from response: %s", e.response.text[:200]
            )
    # As a fallback, if no valid message was captured, covert the exception to string
    # because most of the social-core exceptions implement a valid conversion.
    if isinstance(e, SocialAuthBaseException) and not message:
        message = str(e)
    return message


def log_exception(error):
    err_msg = error.args[0] if error.args else ""
    if getattr(error, "response", None) is not None:
        try:
            err_data = error.response.json()
        except (ValueError, AttributeError):
            logger.error("%s; %s", error, err_msg)
        else:
            logger.error("%s; %s; %s", error, err_msg, err_data)
    else:
        logger.exception("{%s}; {%s}", error, err_msg)
