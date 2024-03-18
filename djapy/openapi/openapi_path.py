import inspect
import re
from http.client import responses

from django.urls import URLPattern
from pydantic import create_model

from .defaults import REF_MODAL_TEMPLATE
from djapy.core.type_check import schema_type, basic_query_schema
from djapy.schema import Schema

__all__ = ['OpenAPI_Path']


class OpenAPI_Path:
    def set_docstrings(self):
        docstring = inspect.getdoc(self.view_func)
        if docstring:
            lines = docstring.split('\n')
            self.summary = lines[0]
            self.explanation = '\n'.join(lines[1:])
        else:
            self.summary = self.view_func.__name__
            self.explanation = ""

    def set_tags(self):
        explicit_tags = (
                getattr(self.view_func, 'openapi_tags', None)
                or self.openapi_tags
                or [self.view_func.__module__]
        )
        self.tags = explicit_tags

    def set_security(self):
        self.security.append(self.view_func.auth_mechanism.app_schema())
        self.export_security_schemes.update(self.view_func.auth_mechanism.schema())

    def __init__(self, url_pattern: URLPattern, parent_url_pattern: list[URLPattern] = None):
        self.parent_url_pattern = parent_url_pattern or []
        self.view_func = url_pattern.callback
        self.openapi_tags = getattr(self.view_func, 'openapi_tags', [])
        self.export_tags = None
        self.export_security_schemes = {}
        self.export_components = {}
        self.export_definitions = {}

        self.security = []
        self.tags = None
        self.explanation = None
        self.summary = None
        self.url_pattern = url_pattern

        self.operation_id = f"{self.view_func.__module__}.{self.view_func.__name__}"
        self.methods = url_pattern.callback.djapy_allowed_method
        self.parameters_keys = []
        self.request_body = {}
        self.responses = {}
        self.parameters = []
        self.path = None
        self.set_path()
        self.set_security()
        self.set_docstrings()
        self.set_tags()
        self.set_parameters()
        self.set_responses()
        self.set_request_body()

    def set_request_body(self):
        if self.view_func.single_data_schema:
            prepared_schema = self.view_func.single_data_schema.model_json_schema(ref_template=REF_MODAL_TEMPLATE)
        else:
            prepared_schema = self.view_func.data_schema.model_json_schema(ref_template=REF_MODAL_TEMPLATE)
        if "$defs" in prepared_schema:
            self.export_components.update(prepared_schema.pop("$defs"))
        content = prepared_schema if prepared_schema["properties"] else {}
        if content:
            self.request_body = {
                "content": {"application/json": {"schema": content}}
            }

    @staticmethod
    def make_parameters(name, schema, required, in_="query"):
        return {
            "name": name,
            "in": in_,
            "required": required,
            "schema": schema
        }

    def set_parameters(self):
        self.set_parameters_from_parent_url_pattern()
        self.set_parameters_from_required_params()

    def set_parameters_from_required_params(self):
        prepared_query_schema = self.view_func.query_schema.model_json_schema(
            ref_template=REF_MODAL_TEMPLATE)  # possibly, this should be a property, no refs
        if prepared_query_schema["properties"]:
            for name, schema in prepared_query_schema["properties"].items():
                if name in self.parameters_keys:
                    continue
                is_url_param = re.search(name, str(self.url_pattern.pattern))
                required_ = name in prepared_query_schema.get("required", [])
                parameter = self.make_parameters(name, schema, required_, "path" if is_url_param else "query")
                self.parameters_keys.append(name)
                self.parameters.append(parameter)

    def set_parameters_from_parent_url_pattern(self):
        for url_pattern in self.parent_url_pattern + [self.url_pattern]:
            pattern = '[<](?:(?P<type>\w+?):)?(?P<name>\w+)[>]'
            if match := re.search(pattern, str(url_pattern.pattern)):
                _type, name = match.groups()
                schema = basic_query_schema(_type)
                parameter = self.make_parameters(name, schema, True, "path")
                self.parameters_keys.append(name)
                self.parameters.append(parameter)

    def set_path(self):
        url_path_string = ""
        for url_pattern in self.parent_url_pattern or []:
            url_path_string += self.format_pattern(url_pattern)
        url_path_string += self.format_pattern(self.url_pattern)
        if not url_path_string.startswith('/'):
            url_path_string = '/' + url_path_string
        self.path = url_path_string

    @staticmethod
    def format_pattern(url_pattern: URLPattern) -> str:
        pattern = '[<](?:(?P<type>\w+?):)?(?P<variable>\w+)[>]'
        match = re.search(pattern, str(url_pattern.pattern))
        if match:
            return re.sub(pattern, '{' + match.group('variable') + '}', str(url_pattern.pattern))
        else:
            return str(url_pattern.pattern)

    @staticmethod
    def make_description_from_status(status: int) -> str:
        return responses.get(status, "Unknown")

    def set_responses(self):
        for status, schema in self.url_pattern.callback.schema.items():
            description = ""
            if schema_type(schema) and schema.Info.description:
                description = schema.Info.description.get(status, "Unknown")
            if not description:
                description = self.make_description_from_status(status)
            response_model = create_model(
                'openapi_response_model',
                **{'response': (schema, ...)},
                __base__=Schema
            )

            prepared_schema = response_model.model_json_schema(ref_template=REF_MODAL_TEMPLATE, mode='serialization')
            if "$defs" in prepared_schema:
                self.export_components.update(prepared_schema.pop("$defs"))
            content = prepared_schema['properties']['response']
            self.responses[str(status)] = {
                "description": description,
                "content": {"application/json": {"schema": content}}
            }

    def dict(self):

        return {
            method.lower(): {
                "summary": self.summary,
                "description": self.explanation,
                "operationId": self.operation_id,
                "responses": self.responses,
                "parameters": self.parameters,
                "requestBody": self.request_body,
                "tags": self.tags,
                "security": self.security
            } for method in self.methods
        }
