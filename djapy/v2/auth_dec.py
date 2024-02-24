import inspect
import json
from functools import wraps
from typing import Dict, Callable, List

from django.http import HttpRequest, JsonResponse

from djapy.v2.defaults import ALLOW_METHODS_LITERAL, DEFAULT_AUTH_REQUIRED_MESSAGE, DEFAULT_METHOD_NOT_ALLOWED_MESSAGE


def djapy_login_required(view_func_or_message_dict: Callable | Dict[str, str] = None) -> Callable:
    message_response = DEFAULT_AUTH_REQUIRED_MESSAGE
    if isinstance(view_func_or_message_dict, dict):
        message_response = view_func_or_message_dict

    try:
        json.dumps(message_response)
    except TypeError as e:
        raise TypeError(f"Invalid message_response: {message_response}") from e

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            view_func.djapy_message_response = message_response
            return view_func(request, *args, **kwargs)

        _wrapped_view.djapy_has_login_required = True
        return _wrapped_view

    if inspect.isfunction(view_func_or_message_dict):
        return decorator(view_func_or_message_dict)

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
