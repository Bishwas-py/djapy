import json
from typing import Callable, Any, Type

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


def get_request_value(request_data: Type[QueryDict] | QueryDict, field_name: str, field_type: type) -> Any | None:
    """
    Helper function to retrieve and convert request data. If the field name is not in the request data, it will return
    None. Later on, another function wil use to know if the field is None, and return
    an JsonResponse error response.
    :param request_data: The request data.
    :param field_name: The name of the field.
    :param field_type: The type of the field.
    :return: The converted request data.
    """
    if field_name in request_data:
        return field_type(request_data[field_name])
    return None


def get_request_data(request):
    content_type = request.META.get('CONTENT_TYPE', '')
    if content_type.startswith('multipart'):
        request_data, _multi_value_dict = MultiPartParser(
            request.META, request,
            request.upload_handlers
        ).parse()
    elif content_type == "application/json":
        request_data = json.loads(request.body)
    else:
        request_data = QueryDict(request.body)
    return request_data
