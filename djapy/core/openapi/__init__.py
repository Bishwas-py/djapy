import base64
import inspect
import json
import re
from http.client import responses
from pathlib import Path
from typing import Optional
from uuid import uuid4

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import URLPattern, get_resolver, path, reverse
from pydantic import create_model

from djapy.schema import Schema
from ..type_check import basic_query_schema, schema_type

ABS_TPL_PATH = Path(__file__).parent.parent.parent / "templates/djapy/"

REF_MODAL_TEMPLATE = "#/components/schemas/{model}"


class OpenApiPath:
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
        explicit_tags = (getattr(self.view_func, 'openapi_tags', None) or self.openai_info.get('tags')
                         or [self.view_func.__module__])
        self.tags = explicit_tags
        self.export_tags = self.openai_info.get('tags_info', [])

    def __init__(self, url_pattern: URLPattern, parent_url_pattern: list[URLPattern] = None):
        self.export_tags = None
        self.tags = None
        self.explanation = None
        self.summary = None
        self.url_pattern = url_pattern
        self.parent_url_pattern = parent_url_pattern or []
        self.view_func = url_pattern.callback
        self.operation_id = f"{self.view_func.__module__}.{self.view_func.__name__}"
        self.openai_info = getattr(self.view_func, 'openapi_info', {})
        self.methods = url_pattern.callback.djapy_allowed_method
        self.export_components = {}
        self.export_definitions = {}
        self.parameters_keys = []
        self.request_body = {}
        self.responses = {}
        self.parameters = []
        self.path = self.get_path_string()
        self.set_docstrings()
        self.set_tags()
        self.set_parameters()
        self.set_responses()
        self.set_request_body()

    def set_request_body(self):
        if len(self.view_func.required_params) == 1 and (schema := schema_type(self.view_func.required_params[0])):
            prepared_schema = schema.schema(ref_template=REF_MODAL_TEMPLATE)
        else:
            prepared_schema = self.view_func.data_schema.schema(ref_template=REF_MODAL_TEMPLATE)
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
        prepared_query_schema = self.view_func.query_schema.schema(
            ref_template=REF_MODAL_TEMPLATE)  # possibly, this should be a property, no refs
        if prepared_query_schema["properties"]:
            for name, schema in prepared_query_schema["properties"].items():
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

    def get_path_string(self) -> str:
        url_path_string = ""
        for url_pattern in self.parent_url_pattern or []:
            url_path_string += self.format_pattern(url_pattern)
        url_path_string += self.format_pattern(self.url_pattern)
        if not url_path_string.startswith('/'):
            url_path_string = '/' + url_path_string
        return url_path_string

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
            if schema_type(schema) and schema.Info.description:
                description = schema.Info.description
            else:
                description = self.make_description_from_status(status)
            response_model = create_model(
                'openapi_response_model',
                **{'response': (schema, ...)},
                __base__=Schema
            )

            prepared_schema = response_model.schema(ref_template=REF_MODAL_TEMPLATE)
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
                "tags": self.tags
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
    description = "Powerful djapy powered API, built with Django and Pydantic"
    info = Info("Djapy", "1.0.0", description)
    paths = {}
    components = {"schemas": {}}
    definitions = {}
    tags = []

    def __init__(self):
        self.resolved_url = get_resolver()

    @staticmethod
    def is_djapy_openapi(view_func):
        return getattr(view_func, 'djapy', False) and getattr(view_func, 'openapi', False)

    def set_path_and_exports(self, openapi_path: OpenApiPath):
        if openapi_path.export_definitions:
            self.definitions.update(path.export_definitions)
        if openapi_path.export_components:
            self.components["schemas"].update(openapi_path.export_components)
        if openapi_path.export_tags:
            self.tags.extend(openapi_path.export_tags)
        if getattr(openapi_path.url_pattern.callback, 'openapi', False):
            self.paths[openapi_path.path] = openapi_path.dict()

    def generate_paths(self, url_patterns: list[URLPattern], parent_url_patterns=None):
        if parent_url_patterns is None:
            parent_url_patterns = []
        for url_pattern in url_patterns:
            if self.is_djapy_openapi(url_pattern.callback):
                openapi_path = OpenApiPath(url_pattern, parent_url_patterns)
                self.set_path_and_exports(openapi_path)
            if hasattr(url_pattern, 'url_patterns'):
                self.generate_paths(url_pattern.url_patterns, parent_url_patterns + [url_pattern])

    def dict(self):
        self.generate_paths(self.resolved_url.url_patterns)
        return {
            'openapi': self.openapi,
            'info': self.info.dict(),
            'paths': self.paths,
            'components': self.components,
            '$defs': self.definitions,
            'tags': self.tags
        }

    def set_basic_info(self, title: str, description, version="1.0.0"):
        self.info.title = title
        self.info.description = description
        self.info.version = version

    def get_openapi(self, request):
        return JsonResponse(self.dict())

    @staticmethod
    def render_swagger_ui(request):
        openapi_json_url = reverse('djapy:openapi')
        absolute_openapi_json_url = request.build_absolute_uri(openapi_json_url)
        return _render_cdn_template(request, ABS_TPL_PATH / 'swagger_cdn.html', {
            "swagger_settings": json.dumps({
                "url": absolute_openapi_json_url,
                "layout": "BaseLayout",
                "deepLinking": "true",
            })
        })

    def get_urls(self):
        return [
            path('openapi.json', self.get_openapi, name='openapi'),
            path('', self.render_swagger_ui, name='swagger'),
        ]

    @property
    def urls(self):
        return self.get_urls(), "djapy", "djapy-openapi"


def _render_cdn_template(
        request: HttpRequest, template_path: Path, context: Optional[dict] = None
) -> HttpResponse:
    "this is helper to find and render html template when ninja is not in INSTALLED_APPS"
    from django.template import RequestContext, Template

    tpl = Template(template_path.read_text())
    html = tpl.render(RequestContext(request, context))
    return HttpResponse(html)


openapi = OpenAPI()
