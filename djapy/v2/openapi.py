import json
import re

from django.urls import URLPattern, get_resolver
from pydantic import create_model

from djapy.schema import Schema

QUERY_BASIC_TYPES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean"
}


class Path:
    path: str
    methods: str
    summary: str
    operation_id: str
    responses: dict
    parameters: list
    export_components: dict
    export_definitions: dict

    def __init__(self, url_pattern: URLPattern, methods: str):
        self.url_pattern = url_pattern
        self.path = self.make_path_name_from_url()
        self.methods = methods
        self.summary = "Register and login user"
        self.export_components = {}
        self.export_definitions = {}
        self.parameters_keys = []
        self.parameters = self.get_parameters(url_pattern.callback)
        self.responses = self.get_responses(url_pattern.callback)
        self.request_body = self.get_request_body(url_pattern.callback)

    def get_request_body(self, view_func):
        request_model_dict = {}
        for param in view_func.required_params:
            if param.name in self.parameters_keys:
                continue
            request_model_dict[param.name] = param.annotation
        if not request_model_dict:
            return {}

        request_model = create_model(
            'openapi_request_model',
            **request_model_dict,
            __base__=Schema
        )
        prepared_schema = request_model.schema(ref_template="#/components/schemas/{model}")
        print(prepared_schema)
        if "$defs" in prepared_schema:
            self.export_components.update(prepared_schema.pop("$defs"))
        content = prepared_schema
        request_body = {
            "content": {"application/json": {"schema": content}}
        }
        return request_body

    def get_parameters(self, view_func):
        parameters = []
        for param in getattr(view_func, 'required_params', []):
            if param.annotation.__name__ in QUERY_BASIC_TYPES:
                schema = {"type": QUERY_BASIC_TYPES.get(param.annotation.__name__, param.annotation.__name__)}
                parameter = {
                    "name": param.name,
                    "in": "path" if self.url_pattern.pattern.regex.pattern.find(param.name) != -1 else "query",
                    "required": True,
                    "schema": schema
                }
                self.parameters_keys.append(param.name)
                parameters.append(parameter)
        return parameters

    def make_path_name_from_url(self) -> str:
        """
        :param url_: A URLResolver object
        :return: A string that represents the path name of the url
        """
        new_path = re.sub('<(.+?):(.+?)>', '{\g<2>}', str(self.url_pattern.pattern))
        return "/" + new_path

    def get_responses(self, view_func):
        responses = {}
        for status, schema in getattr(view_func, 'schema', {}).items():
            description = "OK" if status == 200 else "Else 200"
            response_model = create_model(
                'openapi_response_model',
                **{'response': (schema, ...)},
                __base__=Schema
            )

            prepared_schema = response_model.schema(ref_template="#/components/schemas/{model}")
            if "$defs" in prepared_schema:
                self.export_components.update(prepared_schema.pop("$defs"))
            content = prepared_schema['properties']['response']
            responses[str(status)] = {
                "description": description,
                "content": {"application/json": {"schema": content}}
            }

        return responses

    def dict(self):
        self.operation_id = self.url_pattern.callback.__name__
        return {
            method.lower(): {
                "summary": self.summary,
                "operationId": self.operation_id,
                "responses": self.responses,
                "parameters": self.parameters,
                "requestBody": self.request_body
            } for method in self.methods
        }


class Info:
    def __init__(self, title: str, version: str, description: str):
        self.title = title
        self.version = version
        self.description = description

    def dict(self):
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description
        }


class OpenAPI:
    openapi = "3.1.0"
    description = "This API is a powerful"
    info = Info("My API", "1.0.0", description)
    paths = {}
    components = {"schemas": {}}
    definitions = {}

    def __init__(self):
        self.resolved_url = get_resolver()

    @staticmethod
    def make_path_name_from_url(url_: URLPattern) -> str:
        """
        :param url_: A URLResolver object
        :return: A string that represents the path name of the url
        """
        new_path = re.sub('<int:(.+?)>', '{\g<1>}', str(url_.pattern))
        return new_path

    #
    # def get_interface_details(self, view_func):
    #     if not hasattr(view_func, 'openapi') or not view_func.openapi:
    #         return {}
    #
    #     interface_details = {}
    #     for method in getattr(view_func, 'djapy_allowed_method', []):
    #         interface_details[method.lower()] = {
    #             "operationId": view_func.__name__,
    #             "summary": "Register and login user",
    #             "parameters": [],
    #             "responses": self.get_responses(view_func)
    #         }
    #     return interface_details

    def generate_paths(self, url_pattern: list[URLPattern]):
        for url_pattern in url_pattern:
            if getattr(url_pattern.callback, 'djapy', False) and getattr(url_pattern.callback, 'openapi', False):
                path = Path(url_pattern, url_pattern.callback.djapy_allowed_method)
                if path.export_definitions:
                    self.definitions.update(path.export_definitions)
                if path.export_components:
                    self.components["schemas"].update(path.export_components)
                if getattr(url_pattern.callback, 'openapi', False):
                    self.paths[path.path] = path.dict()
            if hasattr(url_pattern, 'url_patterns'):
                self.generate_paths(url_pattern.url_patterns)

    def dict(self):
        self.generate_paths(self.resolved_url.url_patterns)
        return {
            'openapi': self.openapi,
            'info': self.info.dict(),
            'paths': self.paths,
            'components': self.components,
            '$defs': self.definitions
        }


openapi = OpenAPI()
