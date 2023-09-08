import types

from django.db import models
from django.http import JsonResponse

from djapy.utils.mapper import DjapyModelJsonMapper, DjapyObjectJsonMapper


def node_to_json_response(func):
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param func: A function that returns a JsonNodify object.
    :return: A JsonResponse.
    """

    def wrapper(*args, **kwargs) -> JsonResponse:
        json_node = func(*args, **kwargs)
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

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            model_object = func(request, *args, **kwargs)
            if isinstance(model_object, models.Model) or isinstance(model_object, models.QuerySet):
                return DjapyModelJsonMapper(model_object, model_fields, is_strictly_bounded=is_strictly_bounded)
            return model_object

        return wrapper

    return decorator


def object_to_json_node(object_fields: set | list | str, exclude_null_fields: bool = False) -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param object_fields: A function that returns a JsonNodify object.
    :param exclude_null_fields: Boolean value to indicate whether null fields should be excluded.
    :return: A JsonResponse.
    """
    if not isinstance(object_fields, (set, list, str)):
        raise TypeError('object_fields must be a set, list or str')

    if isinstance(object_fields, str):
        object_fields = [object_fields]
    else:
        object_fields = set(object_fields)

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            raw_object = func(request, *args, **kwargs)
            if isinstance(raw_object, JsonResponse):
                return raw_object
            if isinstance(raw_object, object):
                return DjapyObjectJsonMapper(raw_object, object_fields, exclude_null_fields=exclude_null_fields)
            return raw_object

        return wrapper

    return decorator


def method_to_view(func):
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param func: A function that returns a JsonNodify object.
    :return: A JsonResponse.
    """

    def wrapper(request, *args, **kwargs):
        view_dicts = func(request, *args, **kwargs)
        view_or_model = view_dicts[request.method.lower()]
        if callable(view_or_model):
            if isinstance(view_or_model, types.MethodType):  # models are methods
                return view_or_model()
            elif isinstance(view_or_model, types.FunctionType):  # views are functions
                return view_or_model(request, *args, **kwargs)

    return wrapper
