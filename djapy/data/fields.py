import json

import json
import dataclasses

from typing import Callable

from django.db import models
from django.http import QueryDict
from django.http.multipartparser import MultiPartParser


def get_field_object(field_object_callable: Callable[[], object]) \
        -> tuple[object, list[str, type]] | tuple[None, None]:
    """
    Helper function to retrieve the field object and its annotations. Will return None if the field object is not
    annotated. We discourage using Django models as field objects that's why we raise an error if the field object is
    a Django model.
    :param field_object_callable: A callable that returns the field object.
    :return: A tuple of the field object and its annotations.
    """
    if field_object_callable and callable(field_object_callable):
        field_object = field_object_callable()
        if isinstance(field_object, object) and hasattr(field_object, '__annotations__'):
            field_items = field_object.__annotations__.items()
            return field_object, field_items or []
        elif isinstance(field_object, models.Model):
            raise TypeError('Models are not yet supported')
        else:
            raise TypeError('Query must be a plain object with annotations')
    return None, None


def get_request_value(request_data, field_name, field_type):
    """
    Fetches a specified value from a request dictionary and attempts to cast it to a specified type.

    :param request_data: dict
        A dictionary-like object containing request data. This is typically a Django HttpRequest object but can be a dict-like object as well.
    :param field_name: str
        The name of the field to fetch from `request_data`.
    :param field_type: type or tuple of types
        The type to cast the fetched value to. If a tuple of types is specified, the function will try casting to each type in order, using the first successful cast.
    :return: varied
        The fetched value from the request data, casted to `field_type`. If the value is not found in the request data, `None` is returned. If the value cannot be casted to `field_type`, it is returned as-is.
    """

    field_value = request_data.get(field_name)
    if field_value:
        if dataclasses.is_dataclass(field_type):
            field_value = field_type(**json.loads(field_value))
        elif hasattr(field_type, '__args__'):
            for typ in field_type.__args__:
                try:
                    field_value = typ(field_value)
                    break
                except ValueError:
                    continue
        else:
            field_value = field_type(field_value)
    return field_value


def get_request_data(request):
    content_type = request.META.get('CONTENT_TYPE', '')
    if content_type.startswith('multipart'):
        request_data, _multi_value_dict = MultiPartParser(
            request.META, request,
            request.upload_handlers
        ).parse()
    elif content_type == "application/json":
        request_data = json.loads(request.body)
    elif request.body:
        request_data = QueryDict(request.body)
    else:
        request_data = {}
    return request_data
