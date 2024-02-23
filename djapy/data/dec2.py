import dataclasses
import inspect
import json
from functools import wraps
from typing import Callable, Dict, Type, List, Literal

from django.http import HttpRequest, JsonResponse, HttpResponse, QueryDict
from pydantic import ValidationError

from djapy.schema import Schema
from djapy.utils.prepare_exception import log_exception

SESSION_AUTH = "SESSION"
DEFAULT_AUTH_REQUIRED_MESSAGE = {"message": "You are not logged in", "alias": "auth_required"}
DEFAULT_METHOD_NOT_ALLOWED_MESSAGE = {"message": "Method not allowed", "alias": "method_not_allowed"}
ALLOW_METHODS = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT"]
DEFAULT_MESSAGE_ERROR = {"message": "Something went wrong", "alias": "server_error"}


def make_openapi_response(schema_or_dict: Schema | Dict[int, Schema]):
    if isinstance(schema_or_dict, dict):
        responses = {}
        for status, schema in schema_or_dict.items():
            responses[str(status)] = {
                "description": "OK" if status == 200 else "Error",
                "content": {
                    "application/json": {
                        "schema": schema.model_json_schema() if issubclass(schema, Schema) else schema
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
                                                                               Schema) else schema_or_dict
                }
            }
        }
    }


def extract_and_validate_request_params(request, required_params: list) -> dict:
    parsed_data = {}
    for param in required_params:
        param_type = param.annotation
        if issubclass(param_type, Schema):
            data_dict = {}
            if getattr(param_type.Config, "is_query", False):
                parsed_data[param.name] = param_type(**request.GET.dict())
                continue
            if request.POST:
                data_dict.update(request.POST.dict())
            elif request.body:
                data_dict.update(json.loads(request.body))
            parsed_data[param.name] = param_type(**data_dict)
    return parsed_data


def djapify(schema_or_view_func: Schema | Callable | Dict[int, Type[Schema]],
            login_required: bool = False,
            allowed_method: ALLOW_METHODS | List[ALLOW_METHODS] = "GET",
            ) -> Callable:
    """
    :param schema_or_view_func: A pydantic model or a view function
    :param login_required: A boolean to check if the view requires login
    :param allowed_method: A string or a list of strings to check if the view allows the method
    :return: A decorator that will return a JsonResponse with the schema validated data or a message
    """

    if not isinstance(schema_or_view_func, dict):
        schema_or_view_func = {200: schema_or_view_func}

    def decorator(view_func):
        signature = inspect.signature(view_func)
        exclude_args = [name for name, param in signature.parameters.items() if param.kind == param.VAR_POSITIONAL]
        exclude_kwargs = [name for name, param in signature.parameters.items() if param.kind == param.VAR_KEYWORD]
        required_params = [param for name, param in signature.parameters.items() if
                           param.kind == param.POSITIONAL_OR_KEYWORD and name not in [
                               "request"] and name not in exclude_args and name not in exclude_kwargs]

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
            try:
                kwargs_ = parse_and_return(request, required_params)
            except ValidationError as e:
                return HttpResponse(content=e.json(), content_type="application/json", status=400)

            try:
                func = view_func(request, *args, **kwargs_, **kwargs)
            except Exception as e:
                error_message, display_message = log_exception(request, e)
                return JsonResponse(
                    {"message": display_message, "error_message": error_message, "alias": "server_error"},
                    status=500)

            schema = schema_or_view_func.get(200)
            if issubclass(schema, Schema):
                try:
                    validated_data = schema.model_validate(func)
                    return JsonResponse(validated_data.dict(), status=200)
                except ValidationError as e:
                    return HttpResponse(content=e.json(), content_type="application/json", status=400)

            if callable(schema):
                return JsonResponse(schema(func), status=200, safe=False)

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
