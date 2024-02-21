import inspect
import json
from functools import wraps
from typing import Callable, Dict, Type, List

from django.http import HttpRequest, JsonResponse
from pydantic import BaseModel, InstanceOf
from pydantic_core.core_schema import IsSubclassSchema

SESSION_AUTH = "SESSION"
DEFAULT_AUTH_REQUIRED_MESSAGE = {"message": "You are not logged in"}


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
            method: str | List[str] = "GET",
            ) -> Callable:
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            # Check if `djapy_login_required` decorator is applied
            if getattr(view_func, 'has_django_login_required', False) and not request.user.is_authenticated:
                return JsonResponse(getattr(view_func, 'message_response', DEFAULT_AUTH_REQUIRED_MESSAGE), status=401)

            func = view_func(request, *args, **kwargs)
            if isinstance(schema_or_view_func, dict):
                schema = schema_or_view_func.get(200, None)
            else:
                schema = schema_or_view_func
            return JsonResponse(schema.model_validate(func), status=200)

        if inspect.isclass(schema_or_view_func) or isinstance(schema_or_view_func, dict):
            _wrapped_view.djapy = True
            _wrapped_view.openapi = make_openapi_response(schema_or_view_func)

        return _wrapped_view

    return decorator


def djapy_login_required(view_func_or_message_dict: Callable | Dict[str, str] = None) -> Callable:
    message_response = DEFAULT_AUTH_REQUIRED_MESSAGE
    if isinstance(view_func_or_message_dict, dict):
        message_response = view_func_or_message_dict

    json.dumps(message_response)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            return view_func(request, *args, **kwargs)

        _wrapped_view.has_django_login_required = True
        _wrapped_view.message_response = message_response
        return _wrapped_view

    if inspect.isfunction(view_func_or_message_dict):
        return decorator(view_func_or_message_dict)

    return decorator
