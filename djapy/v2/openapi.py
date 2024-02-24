import re

from django.urls import URLPattern, get_resolver

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
    return f"/{url_.pattern}".replace("<", "{").replace(">", "}")


class OpenAPI:
    def __init__(self):
        self.resolved_url = get_resolver()
        self.openapi_dict = {
            "openapi": "3.1.0",
            "info": {
                "title": "My API",
                "version": "1.0.0"
            },
            "description": "This API is a powerful",
        }

        self.prepared_schemas = {}
        self.prepared_definitions = {}
        self.prepared_parameters = {}
        self.paths = {}

    def get_interface_details(self, view_func):
        if not hasattr(view_func, 'openapi') or not view_func.openapi:
            return {}

        interface_details = {}
        for method in getattr(view_func, 'djapy_allowed_method', []):
            interface_details[method.lower()] = {
                "operationId": view_func.__name__,
                "summary": "Register and login user",
                "parameters": [],
                "responses": self.get_responses(view_func)
            }
        return interface_details

    def get_responses(self, view_func):
        responses = {}
        for status, schema in getattr(view_func, 'schema', {}).items():
            description = "OK" if status == 200 else "Else 200"
            if issubclass(schema, Schema):
                content = {"$ref": f"#/components/schemas/{schema.__name__}"}
                prepared_schema = schema.schema()
                if "$defs" in prepared_schema:
                    self.prepared_definitions.update(prepared_schema.pop("$defs"))
                self.prepared_schemas[schema.__name__] = prepared_schema
            else:
                content = {"type": BASIC_TYPES.get(schema.__name__, "object")}
            responses[str(status)] = {
                "description": description,
                "content": {"application/json": {"schema": content}}
            }
        return responses

    def generate_paths(self, url_patterns):
        for url_pattern in url_patterns:
            path = make_path_name_from_url(url_pattern, url_pattern.callback)
            interface_details = self.get_interface_details(url_pattern.callback)
            if interface_details:
                self.paths[path] = interface_details
            if hasattr(url_pattern, 'url_patterns'):
                self.generate_paths(url_pattern.url_patterns)

    def dict(self):
        self.generate_paths(self.resolved_url.url_patterns)
        return {
            'openapi': self.openapi_dict['openapi'],
            'info': self.openapi_dict['info'],
            'description': self.openapi_dict['description'],
            'paths': self.paths,
            'components': {'schemas': self.prepared_schemas},
            '$defs': self.prepared_definitions
        }


openapi = OpenAPI()
