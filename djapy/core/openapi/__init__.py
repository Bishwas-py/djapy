import inspect
import json
import re
from pathlib import Path
from typing import Optional

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import URLPattern, get_resolver, path, reverse
from pydantic import create_model

from djapy.schema import Schema
from ..type_check import is_param_query_type, param_schema, schema_type

ABS_TPL_PATH = Path(__file__).parent.parent.parent / "templates/djapy/"


class OpenApiPath:
    path: str
    methods: str
    summary: str
    operation_id: str
    responses: dict
    parameters: list
    export_components: dict
    export_definitions: dict
    tags: list
    export_tags: list

    def assign_docstrings(self):
        docstring = inspect.getdoc(self.url_pattern.callback)
        if docstring:
            lines = docstring.split('\n')
            self.summary = lines[0]
            self.explanation = '\n'.join(lines[1:])

    def __init__(self, url_pattern: URLPattern, methods: str):
        self.url_pattern = url_pattern
        self.operation_id = self.url_pattern.callback.__module__ + "." + self.url_pattern.callback.__name__
        openai_info = getattr(self.url_pattern.callback, 'openapi_info', {})
        explicit_tags = (getattr(self.url_pattern.callback, 'openapi_tags', None) or openai_info.get('tags')
                         or [self.url_pattern.callback.__module__])
        self.export_tags = openai_info.get('tags_info', [])
        self.tags = explicit_tags
        self.path = self.make_path_name_from_url()
        self.methods = methods
        self.export_components = {}
        self.export_definitions = {}
        self.parameters_keys = []
        self.summary = ""
        self.explanation = ""
        self.assign_docstrings()
        self.parameters = self.get_parameters(url_pattern.callback)
        self.responses = self.get_responses(url_pattern.callback)
        self.request_body = self.get_request_body(url_pattern.callback)

    def get_request_body(self, view_func):
        request_model_dict = {}
        if len(view_func.required_params) == 1 and (schema := schema_type(view_func.required_params[0])):
            prepared_schema = schema.schema(ref_template="#/components/schemas/{model}")
        else:
            for param in view_func.required_params:
                if param.name in self.parameters_keys:
                    continue
                request_model_dict[param.name] = (param.annotation, ...)
            if not request_model_dict:
                return {}
            request_model = create_model(
                'openapi_request_model',
                **request_model_dict,
                __base__=Schema
            )
            prepared_schema = request_model.schema(ref_template="#/components/schemas/{model}")
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
            if is_param_query_type(param):
                schema = param_schema(param)
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

    @staticmethod
    def make_description_from_status(status: int) -> str:
        status_description = {
            200: "OK",
            201: "Created",
            204: "No Content",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error"
        }
        return status_description.get(status, "Unknown")

    def get_responses(self, view_func):
        responses = {}
        for status, schema in getattr(view_func, 'schema', {}).items():
            if hasattr(schema, 'Info') and getattr(schema.Info, 'description', ""):
                description = schema.Info.description
            else:
                description = self.make_description_from_status(status)
            print(description)
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
    def make_path_name_from_url(url_: URLPattern) -> str:
        """
        :param url_: A URLResolver object
        :return: A string that represents the path name of the url
        """
        new_path = re.sub('<int:(.+?)>', '{\g<1>}', str(url_.pattern))
        return new_path

    def generate_paths(self, url_pattern: list[URLPattern]):
        for url_pattern in url_pattern:
            if getattr(url_pattern.callback, 'djapy', False) and getattr(url_pattern.callback, 'openapi', False):
                path = OpenApiPath(url_pattern, url_pattern.callback.djapy_allowed_method)
                if path.export_definitions:
                    self.definitions.update(path.export_definitions)
                if path.export_components:
                    self.components["schemas"].update(path.export_components)
                if path.export_tags:
                    self.tags.extend(path.export_tags)
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
