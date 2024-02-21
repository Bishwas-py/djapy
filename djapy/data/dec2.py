import inspect
import json
from functools import wraps
from typing import Callable, Dict, Type, List, Literal

from django.http import HttpRequest, JsonResponse
from pydantic import BaseModel

SESSION_AUTH = "SESSION"
DEFAULT_AUTH_REQUIRED_MESSAGE = {"message": "You are not logged in", "alias": "auth_required"}
DEFAULT_METHOD_NOT_ALLOWED_MESSAGE = {"message": "Method not allowed", "alias": "method_not_allowed"}
ALLOW_METHODS = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT"]
DEFAULT_MESSAGE_ERROR = {"message": "Something went wrong", "alias": "server_error"}


def make_openapi_response(schema_or_dict: BaseModel | Dict[int, BaseModel]):
    if isinstance(schema_or_dict, dict):
        responses = {}
        for status, schema in schema_or_dict.items():
            responses[str(status)] = {
                "description": "OK" if status == 200 else "Error",
                "content": {
                    "application/json": {
                        "schema": schema.model_json_schema() if issubclass(schema, BaseModel) else schema
                    }
                }
            }
        return responses
    return {
        "200": {
            "description": "OK",
            "content": {
                "application/json": {
                    "schema": schema_or_dict.model_json_schema() if issubclass(schema_or_dict,
                                                                               BaseModel) else schema_or_dict
                }
            }
        }
    }


def djapify(schema_or_view_func: BaseModel | Callable | Dict[int, Type[BaseModel]],
            login_required: bool = False,
            allowed_method: ALLOW_METHODS | List[ALLOW_METHODS] = "GET",
            ) -> Callable:
    """
    :param schema_or_view_func: A pydantic model or a view function
    :param login_required: A boolean to check if the view requires login
    :param allowed_method: A string or a list of strings to check if the view allows the method
    :return: A decorator that will return a JsonResponse with the schema validated data or a message
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            djapy_has_login_required = getattr(_wrapped_view, 'djapy_has_login_required', False)
            djapy_allowed_method = getattr(_wrapped_view, 'djapy_allowed_method', None)

            if djapy_has_login_required and not request.user.is_authenticated:
                return JsonResponse(getattr(view_func, 'djapy_message_response', DEFAULT_AUTH_REQUIRED_MESSAGE),
                                    status=401)
            if isinstance(djapy_allowed_method, list) and request.method not in djapy_allowed_method:
                return JsonResponse(getattr(view_func, 'message_response', DEFAULT_METHOD_NOT_ALLOWED_MESSAGE),
                                    status=405)
            elif isinstance(djapy_allowed_method, str) and request.method != djapy_allowed_method:
                return JsonResponse(getattr(view_func, 'message_response', DEFAULT_METHOD_NOT_ALLOWED_MESSAGE),
                                    status=405)

            func = view_func(request, *args, **kwargs)
            if isinstance(schema_or_view_func, dict):
                schema = schema_or_view_func.get(200, None)
            else:
                schema = schema_or_view_func
            return JsonResponse(schema.model_validate(func), status=200)

        if inspect.isclass(schema_or_view_func) or isinstance(schema_or_view_func, dict):
            _wrapped_view.djapy = True
            _wrapped_view.openapi = make_openapi_response(schema_or_view_func)

        if login_required:
            setattr(_wrapped_view, 'djapy_has_login_required', True)
        if allowed_method:
            setattr(_wrapped_view, 'djapy_allowed_method', allowed_method)

        return _wrapped_view

    return decorator


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
            return view_func(request, *args, **kwargs)

        _wrapped_view.djapy_has_login_required = True
        _wrapped_view.djapy_message_response = message_response
        return _wrapped_view

    if inspect.isfunction(view_func_or_message_dict):
        return decorator(view_func_or_message_dict)

    return decorator


def djapy_method(allowed_method_or_list: ALLOW_METHODS | List[ALLOW_METHODS],
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
                return JsonResponse(message_response, status=405)
            return view_func(request, *args, **kwargs)

        _wrapped_view.djapy_allowed_method = allowed_method_or_list
        _wrapped_view.djapy_message_response = message_response
        return _wrapped_view

    return decorator
