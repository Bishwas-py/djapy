from typing import Dict

from djapy.schema import Schema

BASIC_TYPES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "tuple": "array",
}


def make_openapi_response(view_func: callable,
                          openapi_tags: list[str] = None) -> dict:
    responses = {}
    for status, schema in view_func.schema.items():
        responses[str(status)] = {
            "description": "OK" if status == 200 else "Else 200",
            "content": {
                "application/json": {
                    "schema": "#/components/schemas/" + schema.__name__ if issubclass(schema, Schema) else {
                        "type": BASIC_TYPES.get(schema.__name__, "object")
                    }
                }
            }
        }
    return responses
