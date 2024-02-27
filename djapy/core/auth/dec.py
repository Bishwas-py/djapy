import inspect
import json
from functools import wraps
from typing import Dict, Callable, List, Type

from django.http import HttpRequest, JsonResponse

from . import BaseAuthMechanism
from ..defaults import ALLOW_METHODS_LITERAL, DEFAULT_METHOD_NOT_ALLOWED_MESSAGE


def djapy_auth(auth_mechanism_class: Type[BaseAuthMechanism],
               permissions: List[str] = None) -> Callable:
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            return view_func(request, *args, **kwargs)

        _wrapped_view.auth_mechanism = auth_mechanism_class()
        _wrapped_view.permissions = permissions
        return _wrapped_view

    if inspect.isfunction(auth_mechanism_class):
        return decorator(auth_mechanism_class)

    return decorator


def djapy_method(allowed_method_or_list: ALLOW_METHODS_LITERAL | List[ALLOW_METHODS_LITERAL],
                 message_response: Dict[str, str] = None) -> Callable:
    message_response = message_response or DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
    try:
        json.dumps(message_response)
    except TypeError as e:
        raise TypeError(f"Invalid message_response: {message_response}") from e

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            if request.method not in allowed_method_or_list:
                view_func.djapy_message_response = message_response
            return view_func(request, *args, **kwargs)

        if isinstance(allowed_method_or_list, str):
            _wrapped_view.djapy_allowed_method = [allowed_method_or_list]
        else:
            _wrapped_view.djapy_allowed_method = allowed_method_or_list
        return _wrapped_view

    return decorator
