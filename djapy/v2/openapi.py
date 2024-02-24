import re

from django.urls import URLPattern

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


# /tags/get-all-posts-by-tag/{tag_slug}
def make_path_name_from_url(url_: URLPattern, view_func: callable) -> str:
    """
    :param url_: A URLResolver object
    :param view_func: A view function
    :return: A string that represents the path name of the url
    """
    return str(url_.pattern)


def make_openapi_response(url_: URLPattern,
                          openapi_tags: list[str] = None) -> tuple:
    view_func = url_.callback
    openapi_enabled = getattr(view_func, 'openapi', False)
    if not openapi_enabled:
        return None, None

    responses = {}
    schema_out = None

    for status, schema in view_func.schema.items():
        for allowed_method in view_func.djapy_allowed_method:
            responses[make_path_name_from_url(url_, view_func)] = {
                str(allowed_method).lower(): {
                    "operationId": view_func.__name__,
                    "summary": "Register and login user",
                    "parameters": [],
                    "responses": {
                        str(status): {
                            "description": "OK" if status == 200 else "Else 200",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/" + schema.__name__ if issubclass(schema,
                                                                                                        Schema) else {
                                            "type": BASIC_TYPES.get(schema.__name__, "object")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        if issubclass(schema, Schema):
            schema_out = schema

    return responses, schema_out
