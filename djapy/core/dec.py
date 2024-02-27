import importlib
import inspect
import json
from functools import wraps
from typing import Callable, Dict, Type, List

from django.urls import reverse
from pydantic_core import InitErrorDetails
from djapy.schema import Schema

from django.http import HttpRequest, JsonResponse, HttpResponse
from pydantic import ValidationError, create_model

from .auth import BaseAuthMechanism
from .defaults import ALLOW_METHODS_LITERAL, DEFAULT_AUTH_REQUIRED_MESSAGE, DEFAULT_METHOD_NOT_ALLOWED_MESSAGE, \
    DEFAULT_MESSAGE_ERROR
from .parser import ResponseDataParser, RequestDataParser
from .labels import REQUEST_INPUT_SCHEMA_NAME
import logging

__all__ = ['djapify']

from .response import create_json_from_validation_error, create_validation_error
from .type_check import is_param_query_type

MAX_HANDLER_COUNT = 1
ERROR_HANDLER_MODULE = "djapy_ext.errorhandler"
ERROR_HANDLER_PREFIX = "handle_"


def get_required_params(view_func: Callable) -> List[inspect.Parameter]:
    """Extract required parameters from a function signature, skipping the first one."""
    signature = inspect.signature(view_func)

    required_params = []
    for index, (name, param) in enumerate(signature.parameters.items()):
        if param.kind == param.POSITIONAL_OR_KEYWORD and index != 0:
            required_params.append(param)

    return required_params


_errorhandler_functions = []
try:
    _imported_errorhandler = importlib.import_module(ERROR_HANDLER_MODULE)
    _all_handlers = dir(_imported_errorhandler)
    if len(_all_handlers) > MAX_HANDLER_COUNT:
        logging.warning(
            f"Errorhandler module should not contain more than {MAX_HANDLER_COUNT} handlers. "
            f"We discourage using more than {MAX_HANDLER_COUNT} handlers in errorhandler module.")
    for f in dir(_imported_errorhandler):
        if f.startswith(ERROR_HANDLER_PREFIX):
            _errorhandler_functions.append(getattr(_imported_errorhandler, f))
except Exception as e:
    _imported_errorhandler = None


def handle_error(request, exception):
    """
    Handle custom exception assigned;
    :param request: A django request object
    :param exception: An exception object
    """
    for _errorhandler_function in _errorhandler_functions:
        _function_signature = inspect.signature(_errorhandler_function)
        exception_param = _function_signature.parameters.get('exception')
        if exception.__class__ == exception_param.annotation:
            _data_from_error = _errorhandler_function(request, exception)
            if _data_from_error and isinstance(_data_from_error, dict):
                try:
                    return JsonResponse(_data_from_error, status=400)
                except TypeError as e:
                    logging.exception(e)
                    return JsonResponse(DEFAULT_MESSAGE_ERROR, status=500)
    return None


def set_schema(view_func: Callable, _wrapped_view: Callable):
    query_schema_dict = {}
    data_schema_dict = {}
    for param in view_func.required_params:
        is_query = is_param_query_type(param)
        is_empty = param.default is inspect.Parameter.empty
        if is_empty:
            passable_tuple = (param.annotation, ...)
        else:
            passable_tuple = (param.annotation, param.default)

        if is_query:
            query_schema_dict[param.name] = passable_tuple
        else:
            data_schema_dict[param.name] = passable_tuple

    _wrapped_view.query_schema = view_func.query_schema = create_model(
        REQUEST_INPUT_SCHEMA_NAME,
        **query_schema_dict,
        __base__=Schema
    )

    _wrapped_view.data_schema = view_func.data_schema = create_model(
        REQUEST_INPUT_SCHEMA_NAME,
        **data_schema_dict,
        __base__=Schema
    )


def djapify(view_func: Callable = None,
            allowed_method: ALLOW_METHODS_LITERAL | List[ALLOW_METHODS_LITERAL] = "GET",
            openapi: bool = True,
            tags: List[str] = None,
            auth_mechanism_obj=BaseAuthMechanism()) -> Callable:
    """
    :param view_func: A pydantic model or a view function
    :param auth_mechanism: A class that inherits from BaseAuthMechanism
    :param allowed_method: A string or a list of strings to check if the view allows the method
    :param openapi: A boolean to check if the view should be included in the openapi schema
    :param tags: A list of strings to tag the view in the openapi schema
    :param auth_mechanism_obj: A class that inherits from BaseAuthMechanism
    :return: A decorator that will return a JsonResponse with the schema validated data or a message
    """
    global _errorhandler_functions

    view_func.required_params = get_required_params(view_func)
    view_func_module = importlib.import_module(view_func.__module__)
    openai_info = getattr(view_func_module, 'openapi_info', {})
    in_app_auth_mechanism = getattr(view_func_module, 'auth_mechanism', None)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **view_kwargs):
            message_json_returned = _wrapped_view.auth_mechanism.authenticate(request, *args, **view_kwargs)
            if message_json_returned:
                return JsonResponse(message_json_returned, status=401)

            message_json_returned = _wrapped_view.auth_mechanism.authorize(request, *args, **view_kwargs)
            if message_json_returned:
                return JsonResponse(message_json_returned, status=403)

            djapy_allowed_method = getattr(_wrapped_view, 'djapy_allowed_method', None)
            djapy_message_response = getattr(view_func, 'djapy_message_response', None)

            if request.method not in djapy_allowed_method:
                return JsonResponse(djapy_message_response or DEFAULT_METHOD_NOT_ALLOWED_MESSAGE, status=405)
            try:
                parser = RequestDataParser(request, view_func, view_kwargs)
                _data_kwargs = parser.parse_request_data()
                response_from_view_func = view_func(request, *args, **_data_kwargs)
                if isinstance(response_from_view_func, tuple):
                    status, response = response_from_view_func
                else:
                    status, response = 200, response_from_view_func

                parser = ResponseDataParser(status, response, schema_dict_returned)
                parsed_data = parser.parse_response_data()
                return JsonResponse(parsed_data, status=status, safe=False)

            except Exception as exception:
                logging.exception(exception)

                error_response = handle_error(request, exception)
                if error_response:
                    return error_response

                if isinstance(exception, ValidationError):
                    return JsonResponse(create_json_from_validation_error(exception), status=400, safe=False)

                return JsonResponse(DEFAULT_MESSAGE_ERROR, status=500)

        schema_dict_returned = view_func.__annotations__.get('return', None)
        if not isinstance(schema_dict_returned, dict):
            schema_dict_returned = {200: schema_dict_returned}

        _wrapped_view.djapy = True
        _wrapped_view.openapi = openapi
        _wrapped_view.openapi_tags = tags
        view_func.schema = _wrapped_view.schema = schema_dict_returned
        _wrapped_view.djapy_message_response = getattr(view_func, 'djapy_message_response', None)
        set_schema(view_func, _wrapped_view)
        _wrapped_view.openapi_info = openai_info

        _wrapped_view.auth_mechanism = getattr(view_func, 'auth_mechanism', in_app_auth_mechanism)
        if not _wrapped_view.auth_mechanism:
            _wrapped_view.auth_mechanism = auth_mechanism_obj

        if not getattr(_wrapped_view, 'djapy_allowed_method', None):
            if isinstance(allowed_method, str):
                _wrapped_view.djapy_allowed_method = [allowed_method]
            else:
                _wrapped_view.djapy_allowed_method = allowed_method

        return _wrapped_view

    if callable(view_func):
        return decorator(view_func)

    return decorator
