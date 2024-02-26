from inspect import Parameter
from typing import Union, get_args

from ..schema import Schema

QUERY_BASIC_TYPES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "datetime": "string"
}


def is_param_query_type(param: Parameter):
    """
    Basically checks if the parameter is a basic query type.
    """
    if not param.annotation:
        return False
    annotation = param.annotation
    is_optional = getattr(annotation, "__origin__", None) is Union
    if is_optional:
        # Get the actual type for Optional[T]
        annotation = get_args(annotation)[0]
    return annotation.__name__ in QUERY_BASIC_TYPES, is_optional


def basic_query_schema(param: Parameter | str, default=None):
    if isinstance(param, str):
        type_name = QUERY_BASIC_TYPES.get(param)
    else:
        type_name = QUERY_BASIC_TYPES.get(param.annotation.__name__)
    return {"type": type_name or default}


def schema_type(param: Parameter):
    if hasattr(param.annotation, "Config") and (
            issubclass(param.annotation, Schema) or isinstance(param.annotation, Schema)):
        return param.annotation
    return None
