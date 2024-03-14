import inspect
import types
from inspect import Parameter
from typing import Union, get_args, get_origin, Literal, List, Optional, Annotated

from django.http import HttpResponse, HttpRequest, HttpResponseBase

from ..schema import Schema, Payload

BASIC_TYPES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "datetime": "string",
    "uuid": "uuid"
}

BASIC_URL_QUERY_TYPES = {
    **BASIC_TYPES,
    "slug": "string",
}


def get_type_name(type_, *args):
    if get_origin(type_) in [Literal, List, Union, Optional, *args]:
        return get_type_name(get_args(type_)[0]) if get_args(type_) else None
    return type_.__name__ if hasattr(type_, "__name__") else type(type_).__name__


def is_originally_basic_type(annotation):
    return all(get_type_name(type_) in BASIC_TYPES for type_ in get_args(annotation))


def is_union_of_basic_types(annotation):
    """
    Checks if the type hint is a union of basic types. QUERY_BASIC_TYPES
    str | datetime -> True
    str | int -> True
    str | float -> True
    str | bool -> True
    bool | int -> True
    str | float | int -> True
    str | float | int | bool -> True
    str | list[int] -> False
    str | list[str] -> False
    str | dict -> False
    """
    if not isinstance(annotation, types.UnionType):
        return False
    return is_originally_basic_type(annotation)


def is_base_query_type(annotation):
    """
    Basically checks if the parameter is a basic query type.
    """
    if get_type_name(annotation) in BASIC_TYPES:
        return True
    if is_union_of_basic_types(annotation):
        return True
    return False


def is_annotated_of_basic_types(annotation):
    args = get_args(annotation)
    origin = get_origin(annotation)

    if origin is Annotated:
        inner_type = args[0]  # Get the inner original type
        if is_base_query_type(inner_type):
            return True
    return False


def is_param_query_type(param: Parameter):
    """
    Basically checks if the parameter is a basic query type.
    """

    annotation = param.annotation
    if is_base_query_type(annotation):
        return True
    if is_annotated_of_basic_types(annotation):
        return True

    return False


def basic_query_schema(param: Parameter | str, default=None):
    type_name = None
    if isinstance(param, str):
        type_name = BASIC_URL_QUERY_TYPES.get(param)
    elif param:
        type_name = BASIC_TYPES.get(param.annotation.__name__)
    return {"type": type_name or default}


def schema_type(param: Parameter | object):
    if isinstance(param, Parameter):
        type_object_ = param.annotation
    else:
        type_object_ = param
    if hasattr(type_object_, "Config") and issubclass(type_object_, Schema) or isinstance(type_object_, Schema):
        return type_object_
    return None


def is_django_type(param: Parameter):
    """
    Checks if the parameter is a django type, or payload[str, int, float, bool]
    """
    if inspect.isclass(param.annotation) and issubclass(param.annotation, HttpResponseBase):
        return True
    return False


def is_schemable_type(param: Parameter):
    """
    Checks if the parameter is a schemable type, or payload[str, int, float, bool]
    """
    if inspect.isclass(param.annotation) and inspect.isclass(param.annotation):
        return True
    return False


def is_data_type(param: Parameter):
    """
    Checks if the parameter is a data type, or payload[str, int, float, bool]
    """
    if isinstance(param.annotation, Payload):
        return param.annotation.unquery_type
    if is_django_type(param):
        return None
    if is_schemable_type(param):
        return param.annotation

    return None
