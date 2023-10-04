import types
from functools import wraps

import djapy.utils.types
from django.db import models
from django.http import JsonResponse

from djapy.utils import defaults
from djapy.utils.mapper import DjapyModelJsonMapper, DjapyObjectJsonMapper
from djapy.utils.prepare_exception import log_exception
from djapy.utils.response_format import create_response


def node_to_json_response(view_func: callable) -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.
    Make sure the object received by this is DjapyModelJsonMapper, DjapyObjectJsonMapper.

    :param view_func: A function that returns a JsonNodify object.
    :return: A JsonResponse.
    """

    def wrapper(*args, **kwargs) -> JsonResponse:
        json_node = view_func(*args, **kwargs)
        if isinstance(json_node, (DjapyModelJsonMapper, DjapyObjectJsonMapper)):
            return json_node.nodify()
        return json_node

    return wrapper


def model_to_json_node(
        model_fields: list | str,
        exclude_null_fields: bool = False,
        include_global_field: bool = True,
        object_parser: "djapy.utils.types.FieldParserType" = None) -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param model_fields: A function that returns a JsonNodify object.
    :param exclude_null_fields: Boolean value to indicate whether the model fields are strictly bounded.
    :param include_global_field: Boolean value to indicate whether null fields should be excluded.
    :param object_parser: A dictionary of field parsers to apply to the model fields.
    :return: A JsonResponse.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            model_object_or_queryset_or_view = view_func(request, *args, **kwargs)
            if isinstance(model_object_or_queryset_or_view, models.Model) or isinstance(
                    model_object_or_queryset_or_view, models.QuerySet):
                return DjapyModelJsonMapper(
                    model_objects=model_object_or_queryset_or_view,
                    model_fields=model_fields,
                    exclude_null_fields=exclude_null_fields,
                    include_global_field=include_global_field,
                    object_parser=object_parser
                )
            return model_object_or_queryset_or_view

        return _wrapped_view

    return decorator


def object_to_json_node(
        object_fields: list | str,
        field_parser: "djapy.utils.types.FieldParserType" = None,
        exclude_null_fields: bool = False) -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param object_fields: A function that returns a JsonNodify object.
    :param field_parser: A dictionary of field parsers to apply to the object fields.
    :param exclude_null_fields: Boolean value to indicate whether null fields should be excluded.
    :return: A JsonResponse.
    """
    if not isinstance(object_fields, (list, str)):
        raise TypeError('object_fields must be a set, list or str')

    if isinstance(object_fields, str):
        object_fields = [object_fields]
    else:
        object_fields = set(object_fields)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if callable(view_func):
                raw_object = view_func(request, *args, **kwargs)
            else:
                raw_object = view_func

            if isinstance(raw_object, (JsonResponse, DjapyObjectJsonMapper, DjapyModelJsonMapper)):
                # check if the object is already a JsonResponse or DjapyObjectJsonMapper or DjapyModelJsonMapper object
                # if it is, return it as it is
                return raw_object

            # as a last resort, check if the object is an object, which is true most of the time
            if isinstance(raw_object, object):
                return DjapyObjectJsonMapper(
                    raw_object, object_fields,
                    exclude_null_fields=exclude_null_fields,
                    field_parser=field_parser
                )
            return raw_object

        return _wrapped_view

    return decorator


def method_to_view(view_func: callable) -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param view_func: A function that returns a JsonNodify object.
    :return: A JsonResponse.
    """

    def wrapper(request, *args, **kwargs):
        view_dicts = view_func(request, *args, **kwargs)
        view_or_model = view_dicts[request.method.lower()]
        if callable(view_or_model):
            if isinstance(view_or_model, types.MethodType):  # models are methods
                return view_or_model()
            elif isinstance(view_or_model, types.FunctionType):  # views are functions
                return view_or_model(request, *args, **kwargs)
        return view_or_model

    return wrapper


def catch_errors(view_func: callable) -> callable:
    """
    Use this decorator to catch errors from a view function.

    :param view_func: A view function.
    :return: A JsonResponse.
    """

    def wrapper(request, *args, **kwargs):
        try:
            view_response = view_func(request, *args, **kwargs)
            if isinstance(view_response, dict):
                return JsonResponse(view_response, status=200)
            return view_response
        except Exception as exception:
            error, display_message = log_exception(request, exception)
            error_response = create_response(
                'failed',
                'server_error',
                message=display_message,
                extras={
                    'path': request.path,
                    'error': error,
                }
            )
            return JsonResponse(error_response, status=500)

    return wrapper

