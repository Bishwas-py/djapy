from inspect import Parameter

QUERY_BASIC_TYPES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean"
}


def is_param_query_type(param: Parameter):
    """
    Basically checks if the parameter is a basic query type.
    """
    return param.annotation.__name__ in QUERY_BASIC_TYPES


def param_schema(param: Parameter):
    return {"type": QUERY_BASIC_TYPES.get(param.annotation.__name__, param.annotation.__name__)}


def schema_type(param: Parameter):
    if hasattr(param.annotation, "Config"):
        return param.annotation
    return None
