import importlib
import inspect
from functools import wraps
from typing import Callable, Dict, Type, List

from django.http import HttpRequest, JsonResponse, HttpResponse
from pydantic import ValidationError

from djapy.data.defaults import ALLOW_METHODS, DEFAULT_AUTH_REQUIRED_MESSAGE, DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
from djapy.data.parser import extract_and_validate_request_params
from djapy.schema import Schema
from djapy.utils.prepare_exception import log_exception
import logging

__all__ = ['djapify']

MAX_HANDLER_COUNT = 1


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
    _imported_errorhandler = importlib.import_module("djapy_ext.errorhandler")
    _all_handlers = dir(_imported_errorhandler)
    if len(_all_handlers) > MAX_HANDLER_COUNT:
        logging.warning(
            f"Errorhandler module should not contain more than {MAX_HANDLER_COUNT} handlers. "
            f"We discourage using more than {MAX_HANDLER_COUNT} handlers in errorhandler module.")
    for f in dir(_imported_errorhandler):
        if f.startswith('handler_'):
            _errorhandler_functions.append(getattr(_imported_errorhandler, f))
except Exception as e:
    _imported_errorhandler = None


def djapify(schema_or_view_func: Schema | Callable | Dict[int, Type[Schema]],
            login_required: bool = False,
            allowed_method: ALLOW_METHODS | List[ALLOW_METHODS] = "GET",
            openapi: bool = False,
            openapi_tags: List[str] = None) -> Callable:
    """
    :param schema_or_view_func: A pydantic model or a view function
    :param login_required: A boolean to check if the view requires login
    :param allowed_method: A string or a list of strings to check if the view allows the method
    :param openapi: A boolean to check if the view should be included in the openapi schema
    :param openapi_tags: A list of strings to tag the view in the openapi schema
    :return: A decorator that will return a JsonResponse with the schema validated data or a message
    """
    global _errorhandler_functions

    if not isinstance(schema_or_view_func, dict):
        schema_or_view_func = {200: schema_or_view_func}

    def decorator(view_func):
        required_params = get_required_params(view_func)

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
                _data_kwargs = extract_and_validate_request_params(request, required_params)
                func = view_func(request, *args, **_data_kwargs, **kwargs)

            except Exception as exception:
                for _errorhandler_function in _errorhandler_functions:
                    exception_param = inspect.signature(_errorhandler_function).parameters['exception']
                    if exception.__class__ == exception_param.annotation:
                        _data_from_error = _errorhandler_function(request, exception=exception)
                        if _data_from_error and isinstance(_data_from_error, dict):
                            return JsonResponse(_data_from_error, status=400)
                return exception
            except ValidationError as exception:
                return HttpResponse(content=exception.json(), content_type="application/json", status=400)

            schema = schema_or_view_func.get(200)
            if issubclass(schema, Schema):
                try:
                    validated_data = schema.model_validate(func)
                    return JsonResponse(validated_data.dict(), status=200)
                except ValidationError as exception:
                    return HttpResponse(content=exception.json(), content_type="application/json", status=400)

            if callable(schema):
                return JsonResponse(schema(func), status=200, safe=False)

        if inspect.isclass(schema_or_view_func) or isinstance(schema_or_view_func, dict):
            _wrapped_view.djapy = True
            _wrapped_view.openapi = openapi
            _wrapped_view.openapi_tags = openapi_tags
            _wrapped_view.djapy_message_response = getattr(view_func, 'djapy_message_response', {})

        if login_required:
            setattr(_wrapped_view, 'djapy_has_login_required', True)
        if allowed_method:
            setattr(_wrapped_view, 'djapy_allowed_method', allowed_method)

        return _wrapped_view

    return decorator
