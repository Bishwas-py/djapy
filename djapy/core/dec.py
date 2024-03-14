import importlib
import inspect
import json
from functools import wraps
from typing import Callable, Dict, Type, List

from django.core.serializers.json import DjangoJSONEncoder

from djapy.schema import Schema

from django.http import HttpRequest, JsonResponse, HttpResponse
from pydantic import ValidationError, create_model

from .auth import BaseAuthMechanism, base_auth_obj
from .defaults import ALLOW_METHODS_LITERAL, DEFAULT_METHOD_NOT_ALLOWED_MESSAGE, \
    DEFAULT_MESSAGE_ERROR
from djapy.pagination.base_pagination import BasePagination
from .parser import ResponseDataParser, RequestDataParser, get_response_schema_dict
from .labels import REQUEST_INPUT_SCHEMA_NAME
import logging

__all__ = ['djapify']

from .response import create_json_from_validation_error
from .type_check import is_param_query_type, schema_type, is_data_type

MAX_HANDLER_COUNT = 1
ERROR_HANDLER_MODULE = "djapy_ext.errorhandler"
ERROR_HANDLER_PREFIX = "handle_"
IN_APP_AUTH_MECHANISM_NAME = "AUTH_MECHANISM"
IN_APP_TAGS_NAME = "TAGS"


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
            if isinstance(_data_from_error, JsonResponse):
                return _data_from_error

            if isinstance(_data_from_error, tuple):
                status, response = _data_from_error
            else:
                status, response = 400, _data_from_error
            if response and isinstance(response, dict):
                try:
                    return JsonResponse(response, status=status, safe=False)
                except TypeError as e:
                    logging.exception(e)
                    return JsonResponse(DEFAULT_MESSAGE_ERROR, status=500)
    return None


def get_passable_tuple(param: inspect.Parameter, annotation=None):
    """
    Get a passable tuple from the parameter
    for the pydantic model creation.
    """
    if annotation is None:
        annotation = param.annotation
    is_empty = param.default is inspect.Parameter.empty
    if is_empty:
        passable_tuple = (annotation, ...)
    else:
        passable_tuple = (annotation, param.default)
    return passable_tuple


def get_schemas(required_params: List[inspect.Parameter], extra_query_dict: Dict = None):
    """
    Get the query and data schema from the required parameters. Basically, for input validation.
    :param required_params: A list of required parameters
    :param extra_query_dict: A dictionary of extra query parameters
    """
    query_schema_dict = {}
    data_schema_dict = {}
    if not extra_query_dict:
        extra_query_dict = {}
    for param in required_params:
        is_query = is_param_query_type(param)
        if param.annotation is inspect.Parameter.empty:
            raise TypeError(f"Parameter `{param.name}` should have a type annotation, because it's required. e.g. "
                            f"`def view_func({param.name}: str):`")
        if is_query:
            query_schema_dict[param.name] = get_passable_tuple(param)
        elif data_type := is_data_type(param):
            data_schema_dict[param.name] = get_passable_tuple(param, data_type)

    query_model = create_model(
        REQUEST_INPUT_SCHEMA_NAME,
        **query_schema_dict,
        **extra_query_dict,
        __base__=Schema
    )

    data_model = create_model(
        REQUEST_INPUT_SCHEMA_NAME,
        **data_schema_dict,
        __base__=Schema
    )

    return query_model, data_model


def get_auth(view_func: Callable,
             auth: Type[BaseAuthMechanism] | BaseAuthMechanism | None,
             in_app_auth_mechanism: Type[BaseAuthMechanism] | BaseAuthMechanism | None):
    """
    Set the auth mechanism for the view function

    :param view_func: The view function
    :param auth: The auth mechanism
    :param in_app_auth_mechanism: The auth mechanism in the app or views.py
    """
    auth = getattr(view_func, 'auth_mechanism', None) or auth
    if auth == base_auth_obj and in_app_auth_mechanism:
        wrapped_auth = in_app_auth_mechanism
    elif auth is None:
        return base_auth_obj
    else:
        wrapped_auth = auth

    if inspect.isclass(wrapped_auth) and issubclass(wrapped_auth, BaseAuthMechanism):
        wrapped_auth = wrapped_auth()
    else:
        wrapped_auth = wrapped_auth

    if not wrapped_auth:
        wrapped_auth = base_auth_obj

    if not isinstance(wrapped_auth, BaseAuthMechanism):
        raise TypeError(
            f"auth should be a class that inherits from BaseAuthMechanism, not {wrapped_auth.__name__} or {type(wrapped_auth)}")

    return wrapped_auth


def djapify(view_func: Callable = None,
            allowed_method: ALLOW_METHODS_LITERAL | List[ALLOW_METHODS_LITERAL] = "GET",
            openapi: bool = True,
            tags: List[str] = None,
            auth: Type[BaseAuthMechanism] | BaseAuthMechanism | None = base_auth_obj) -> Callable:
    """
    :param view_func: A pydantic model or a view function
    :param allowed_method: A string or a list of strings to check if the view allows the method
    :param openapi: A boolean to check if the view should be included in the openapi schema
    :param tags: A list of strings to tag the view in the openapi schema
    :param auth: A class that inherits from BaseAuthMechanism
    :return: A decorator that will return a JsonResponse with the schema validated data or a message
    """
    global _errorhandler_functions

    def decorator(view_func):
        view_func.required_params = get_required_params(view_func)
        view_func.in_response_param = None
        for param in view_func.required_params:
            if issubclass(param.annotation, HttpResponse):
                view_func.in_response_param = param
                break
        view_func_module = importlib.import_module(view_func.__module__)
        in_app_auth_mechanism = getattr(view_func_module, IN_APP_AUTH_MECHANISM_NAME, None)

        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **view_kwargs):
            authentication_info_tuple = _wrapped_view.auth_mechanism.authenticate(request, *args, **view_kwargs)
            if authentication_info_tuple:
                return JsonResponse(authentication_info_tuple[1], status=authentication_info_tuple[0])

            authorization_info_tuple = _wrapped_view.auth_mechanism.authorize(request, *args, **view_kwargs)
            if authorization_info_tuple:
                return JsonResponse(authorization_info_tuple[1], status=authorization_info_tuple[0])

            djapy_allowed_method = getattr(_wrapped_view, 'djapy_allowed_method', None)
            djapy_message_response = getattr(view_func, 'djapy_message_response', None)

            if request.method not in djapy_allowed_method:
                return JsonResponse(djapy_message_response or DEFAULT_METHOD_NOT_ALLOWED_MESSAGE, status=405)
            try:
                response = HttpResponse(content_type="application/json")
                parser = RequestDataParser(request, view_func, view_kwargs)
                _input_data = parser.parse_request_data()

                if view_func.in_response_param:
                    _input_data[view_func.in_response_param.name] = response

                response_from_view_func = view_func(request, *args, **_input_data)

                status_code, response_data = response_from_view_func \
                    if isinstance(response_from_view_func, tuple) else (200, response_from_view_func)

                parser = ResponseDataParser(status_code, response_data, schema_dict_returned, request, _input_data)
                parsed_data = parser.parse_response_data()

                response.status_code = status_code
                response.content = json.dumps(parsed_data, cls=DjangoJSONEncoder)
                return response


            except Exception as exception:
                logging.exception(exception)

                error_response = handle_error(request, exception)
                if error_response:
                    return error_response

                if isinstance(exception, ValidationError):
                    return JsonResponse(create_json_from_validation_error(exception), status=400, safe=False)

                return JsonResponse(DEFAULT_MESSAGE_ERROR, status=500)

        schema_dict_returned = get_response_schema_dict(view_func)

        extra_query_dict = getattr(view_func, 'extra_query_dict', {})  # (name: (type_name_, default))
        response_wrapper = getattr(view_func, 'response_wrapper', None)  # (status, schema)

        if response_wrapper:
            status, wrapper_schema = response_wrapper
            if status in schema_dict_returned:
                schema_dict_returned[status] = wrapper_schema[schema_dict_returned[status]]

        _wrapped_view.djapy = True
        _wrapped_view.openapi = openapi
        _wrapped_view.openapi_tags = tags or getattr(view_func_module, IN_APP_TAGS_NAME, [])

        view_func.schema = _wrapped_view.schema = schema_dict_returned
        _wrapped_view.djapy_message_response = getattr(view_func, 'djapy_message_response', None)

        query_schema, data_schema = get_schemas(view_func.required_params, extra_query_dict)
        _wrapped_view.query_schema = view_func.query_schema = query_schema
        _wrapped_view.data_schema = view_func.data_schema = data_schema
        if len(data_schema.__annotations__) == 1:
            single_data_schema = list(data_schema.__annotations__.values())[0]
            single_data_key = list(data_schema.__annotations__.keys())[0]
            if not issubclass(single_data_schema, Schema):
                single_data_schema = None
                single_data_key = None
        else:
            single_data_schema = None
            single_data_key = None

        _wrapped_view.single_data_schema = view_func.single_data_schema = single_data_schema
        _wrapped_view.single_data_key = view_func.single_data_key = single_data_key

        _wrapped_view.auth_mechanism = get_auth(view_func, auth, in_app_auth_mechanism)

        if not getattr(_wrapped_view, 'djapy_allowed_method', None):
            if isinstance(allowed_method, str):
                _wrapped_view.djapy_allowed_method = [allowed_method]
            else:
                _wrapped_view.djapy_allowed_method = allowed_method

        return _wrapped_view

    if callable(view_func):
        return decorator(view_func)

    return decorator
