import types
from functools import wraps

import djapy.utils.types
from django.db import models
from django.http import JsonResponse

from djapy.utils.mapper import DjapyModelJsonMapper, DjapyObjectJsonMapper


def node_to_json_response(view_func: callable) -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param view_func: A function that returns a JsonNodify object.
    :return: A JsonResponse.
    """

    def wrapper(*args, **kwargs) -> JsonResponse:
        json_node = view_func(*args, **kwargs)
        if isinstance(json_node, (DjapyModelJsonMapper, DjapyObjectJsonMapper)):
            return json_node.nodify()
        return json_node

    return wrapper


def model_to_json_node(model_fields: list | str, is_strictly_bounded: bool = False) -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param model_fields: A function that returns a JsonNodify object.
    :param is_strictly_bounded: Boolean value to indicate whether the model fields are strictly bounded.
    :return: A JsonResponse.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            model_object = view_func(request, *args, **kwargs)
            if isinstance(model_object, models.Model) or isinstance(model_object, models.QuerySet):
                return DjapyModelJsonMapper(model_object, model_fields, is_strictly_bounded=is_strictly_bounded)
            return model_object

        return _wrapped_view

    return decorator


def object_to_json_node(object_fields: list | str, field_parser: "djapy.utils.types.FieldParserType" = None,
                        exclude_null_fields: bool = False) -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param object_fields: A function that returns a JsonNodify object.
    :param exclude_null_fields: Boolean value to indicate whether null fields should be excluded.
    :param field_parser: A dictionary of field parsers to apply to the object fields.
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

            if isinstance(raw_object, JsonResponse):
                return raw_object
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

    return wrapper
