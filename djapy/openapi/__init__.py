import json
from pathlib import Path
from typing import Optional, TypedDict

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.urls import URLPattern, get_resolver, path, reverse

from .defaults import ABS_TPL_PATH
from .info import Info, Contact, License
from .openapi_path import OpenAPI_Path


class PassedBaseUrl(TypedDict):
    url: str
    description: str


class OpenAPI:
    openapi = "3.1.0"
    description = "Powerful djapy powered API, built with Django and Pydantic"
    info = Info("Djapy", "1.0.0", description)
    paths = {}
    components = {"schemas": {}}
    definitions = {}
    tags = []
    security_schema = {}
    security = {}
    passed_base_urls = None
    contact = None
    license = None

    def __init__(self):
        self.resolved_url = get_resolver()

    @staticmethod
    def is_djapy_openapi(view_func):
        return getattr(view_func, 'djapy', False) and getattr(view_func, 'openapi', False)

    def set_path_and_exports(self, openapi_path_: OpenAPI_Path):
        if openapi_path_.export_definitions:
            self.definitions.update(path.export_definitions)
        if openapi_path_.export_components:
            self.components["schemas"].update(openapi_path_.export_components)
        if openapi_path_.export_security_schemes:
            self.components["securitySchemes"] = {
                **self.components.get("securitySchemes", {}),
                **openapi_path_.export_security_schemes
            }
        if openapi_path_.export_tags:
            self.tags.extend(openapi_path_.export_tags)
        if getattr(openapi_path_.url_pattern.callback, 'openapi', False):
            self.paths[openapi_path_.path] = openapi_path_.dict()

    def generate_paths(self, url_patterns: list[URLPattern], parent_url_patterns=None):
        if parent_url_patterns is None:
            parent_url_patterns = []
        for url_pattern in url_patterns:
            if self.is_djapy_openapi(url_pattern.callback):
                openapi_path_ = OpenAPI_Path(url_pattern, parent_url_patterns)
                self.set_path_and_exports(openapi_path_)
            if hasattr(url_pattern, 'url_patterns'):
                self.generate_paths(url_pattern.url_patterns, parent_url_patterns + [url_pattern])

    def dict(self, request: HttpRequest):
        self.generate_paths(self.resolved_url.url_patterns)
        servers = [
            {'url': request.build_absolute_uri('/'), 'description': 'Local server'},
        ]
        if self.passed_base_urls:
            servers.extend(self.passed_base_urls)
        return {
            'openapi': self.openapi,
            'info': self.info.dict(),
            'paths': self.paths,
            'components': self.components,
            '$defs': self.definitions,
            'tags': self.tags,
            'security': self.security,
            'servers': servers
        }

    def set_basic_info(
            self, title: str, description, version="1.0.0",
            tags_info=None, security_schema: dict = None,
            security: dict = None,
            passed_base_url: Optional[list[PassedBaseUrl]] = None,
            contact: Contact = None,
            license_: License = None,
    ):
        self.info.title = title
        self.info.description = description
        self.info.version = version
        self.info.contact = contact
        self.info.license = license_
        self.tags.extend(tags_info or [])
        self.security_schema = security_schema or {}
        self.security = security or {}
        self.passed_base_urls = passed_base_url

    def get_openapi(self, request):
        openapi_dict = self.dict(request)
        return JsonResponse(openapi_dict)

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
    "this is helper to find and render html template when djapy is not in INSTALLED_APPS"
    from django.template import RequestContext, Template

    tpl = Template(template_path.read_text())
    html = tpl.render(RequestContext(request, context))
    return HttpResponse(html)


openapi = OpenAPI()
