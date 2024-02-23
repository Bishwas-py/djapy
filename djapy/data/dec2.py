import inspect
from functools import wraps
from typing import Callable, Dict, Type, List

from django.http import HttpRequest, JsonResponse, HttpResponse, QueryDict
from pydantic import ValidationError

from djapy.data.defaults import ALLOW_METHODS, DEFAULT_AUTH_REQUIRED_MESSAGE, DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
from djapy.data.openapi import make_openapi_response
from djapy.data.parser import extract_and_validate_request_params
from djapy.schema import Schema
from djapy.utils.prepare_exception import log_exception


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
                kwargs_ = extract_and_validate_request_params(request, required_params)
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
