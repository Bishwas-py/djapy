import types
from inspect import Parameter
from typing import Union, get_args, get_origin, Literal, List, Optional

from ..schema import Schema

QUERY_BASIC_TYPES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "datetime": "string"
}


def is_literal_of_string(type_hint):
    origin = get_origin(type_hint)
    args = get_args(type_hint) if origin == Literal else []

    return origin == Literal and all(isinstance(arg, str) for arg in args)


def get_type_name(type_):
    if get_origin(type_) in [Literal, List, Union, Optional]:
        return get_type_name(get_args(type_)[0]) if get_args(type_) else None
    return type_.__name__ if hasattr(type_, "__name__") else type(type_).__name__


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

    return all(get_type_name(type_) in QUERY_BASIC_TYPES for type_ in get_args(annotation))


def is_param_query_type(param: Parameter):
    """
    Basically checks if the parameter is a basic query type.
    """

    annotation = param.annotation
    if get_type_name(annotation) in QUERY_BASIC_TYPES:
        return True
    if is_union_of_basic_types(annotation):
        return True
    return False


def basic_query_schema(param: Parameter | str, default=None):
    type_name = None
    if isinstance(param, str):
        type_name = QUERY_BASIC_TYPES.get(param)
    elif param:
        type_name = QUERY_BASIC_TYPES.get(param.annotation.__name__)
    return {"type": type_name or default}


def schema_type(param: Parameter | object):
    if isinstance(param, Parameter):
        object_ = param.annotation
    else:
        object_ = param
    if hasattr(object_, "Config") and (
            issubclass(object_, Schema) or isinstance(object_, Schema)):
        return object_
    return None
