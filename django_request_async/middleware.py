import logging
from concurrent.futures import ThreadPoolExecutor

from django.core.exceptions import ValidationError
from django.utils.deprecation import MiddlewareMixin
from request import settings
from request.models import Request
from request.router import Patterns
from request.utils import request_is_ajax

logger = logging.getLogger("request.security.middleware")

executor = ThreadPoolExecutor(max_workers=1)


def preprocess(request, response):
    if request.method.lower() not in settings.VALID_METHOD_NAMES:
        return response

    if response.status_code < 400 and settings.ONLY_ERRORS:
        return response

    ignore = Patterns(False, *settings.IGNORE_PATHS)
    if ignore.resolve(request.path[1:]):
        return response

    if request_is_ajax(request) and settings.IGNORE_AJAX:
        return response

    if request.META.get("REMOTE_ADDR") in settings.IGNORE_IP:
        return response

    ignore = Patterns(False, *settings.IGNORE_USER_AGENTS)
    if ignore.resolve(request.META.get("HTTP_USER_AGENT", "")):
        return response

    if getattr(request, "user", False):
        if request.user.get_username() in settings.IGNORE_USERNAME:
            return response


def save_request(request, response):
    r = Request()
    try:
        r.from_http_request(request, response, commit=False)
        r.full_clean()
    except ValidationError as exc:
        logger.warning(
            "Bad request: %s",
            str(exc),
            exc_info=exc,
            extra={"status_code": 400, "request": request},
        )
    else:
        r.save()


class RequestMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        preprocess(request, response)
        save_request(request, response)
        return response


class AsyncRequestMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        preprocess(request, response)
        executor.submit(save_request, request, response)
        return response
