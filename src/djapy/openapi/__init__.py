import json
from pathlib import Path
from typing import Optional, TypedDict, Dict, Any
from functools import lru_cache
import hashlib

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.urls import URLPattern, get_resolver, path, reverse
from django.core.cache import cache

from .defaults import ABS_TPL_PATH
from .icons import icons
from .info import Info, Contact, License
from .openapi_path import OpenAPI_Path


class PassedBaseUrl(TypedDict):
   url: str
   description: str


class OpenAPI:
   """Enhanced OpenAPI generator with caching and better performance."""
   
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
   
   # Cache configuration
   _cache_enabled = True
   _cache_timeout = 300  # 5 minutes default
   _schema_cache_key = "djapy:openapi:schema"

   def __init__(self, cache_enabled: bool = True):
      self.resolved_url = get_resolver()
      self._cache_enabled = cache_enabled
      self._path_hash = None

   @staticmethod
   def is_djapy_openapi(view_func):
      return getattr(view_func, 'djapy', False) and getattr(view_func, 'openapi', False)

   def set_path_and_exports(self, openapi_path_: OpenAPI_Path) -> None:
      """Set path and export schemas with better error handling."""
      try:
         if openapi_path_.export_definitions:
            self.definitions.update(openapi_path_.export_definitions)
         if openapi_path_.export_components:
            self.components["schemas"].update(openapi_path_.export_components)
         if openapi_path_.export_security_schemes:
            if "securitySchemes" not in self.components:
               self.components["securitySchemes"] = {}
            self.components["securitySchemes"].update(openapi_path_.export_security_schemes)
         if openapi_path_.export_tags:
            # Only add unique tags
            existing_tag_names = {tag.get('name') for tag in self.tags}
            for tag in openapi_path_.export_tags:
               if tag.get('name') not in existing_tag_names:
                  self.tags.append(tag)
                  existing_tag_names.add(tag.get('name'))
         if getattr(openapi_path_.url_pattern.callback, 'openapi', False):
            self.paths[openapi_path_.path] = openapi_path_.dict()
      except Exception as e:
         # Log error with context but don't break schema generation
         import logging
         view_name = getattr(openapi_path_.url_pattern.callback, '__name__', 'unknown')
         path = getattr(openapi_path_, 'path', 'unknown')
         logging.warning(
            f"Error generating OpenAPI schema for path '{path}' (view: {view_name}): {e}",
            exc_info=True  # Include traceback in debug mode
         )

   def generate_paths(self, url_patterns: list[URLPattern], parent_url_patterns=None):
      if parent_url_patterns is None:
         parent_url_patterns = []
      for url_pattern in url_patterns:
         try:
            if self.is_djapy_openapi(url_pattern.callback):
               openapi_path_ = OpenAPI_Path(url_pattern, parent_url_patterns)
               self.set_path_and_exports(openapi_path_)
            if hasattr(url_pattern, 'url_patterns'):
               self.generate_paths(url_pattern.url_patterns, parent_url_patterns + [url_pattern])
         except Exception as e:
            if url_pattern.callback:
               print(f"[x] Error in generating paths for view: `{url_pattern.callback.__name__}`;")
            raise e

   def _compute_url_hash(self) -> str:
      """Compute hash of URL patterns for cache invalidation."""
      url_repr = str(self.resolved_url.url_patterns)
      return hashlib.md5(url_repr.encode()).hexdigest()

   def dict(self, request: HttpRequest, use_cache: bool = True) -> Dict[str, Any]:
      """Generate OpenAPI schema with optional caching.
      
      Args:
          request: Django HttpRequest
          use_cache: Whether to use cached schema (default: True)
      
      Returns:
          OpenAPI schema dictionary
      """
      # Check cache first
      if use_cache and self._cache_enabled:
         current_hash = self._compute_url_hash()
         cache_key = f"{self._schema_cache_key}:{current_hash}"
         cached_schema = cache.get(cache_key)
         
         if cached_schema:
            # Update dynamic parts (servers)
            cached_schema['servers'][0]['url'] = request.build_absolute_uri('/')
            return cached_schema
      
      # Generate fresh schema
      self.generate_paths(self.resolved_url.url_patterns)
      servers = [
         {'url': request.build_absolute_uri('/'), 'description': 'Local server'},
      ]
      if self.passed_base_urls:
         servers.extend(self.passed_base_urls)
      
      schema = {
         'openapi': self.openapi,
         'info': self.info.dict(),
         'paths': self.paths,
         'components': self.components,
         '$defs': self.definitions,
         'tags': list({tag['name']: tag for tag in self.tags}.values()),  # Deduplicate tags
         'security': self.security,
         'servers': servers
      }
      
      # Cache the result
      if use_cache and self._cache_enabled:
         current_hash = self._compute_url_hash()
         cache_key = f"{self._schema_cache_key}:{current_hash}"
         cache.set(cache_key, schema, self._cache_timeout)
      
      return schema

   def set_basic_info(
     self, title: str, description, version="1.0.0",
     tags_info=None, security_schema: dict = None,
     security: dict = None,
     passed_base_url: Optional[list[PassedBaseUrl]] = None,
     contact: Contact = None,
     license_: License = None,
     site_name="Djapy",
   ):
      self.info.title = title
      self.info.cvar_describe = description
      self.info.version = version
      self.info.contact = contact
      self.info.site_name = site_name
      self.info.license = license_
      self.tags.extend(tags_info or [])
      self.security_schema = security_schema or {}
      self.security = security or {}
      self.passed_base_urls = passed_base_url

   def get_openapi(self, request: HttpRequest) -> JsonResponse:
      """Get OpenAPI schema as JSON response."""
      openapi_dict = self.dict(request)
      return JsonResponse(
         openapi_dict,
         json_dumps_params={'indent': 2}  # Pretty print for better readability
      )
   
   def clear_cache(self) -> None:
      """Clear OpenAPI schema cache."""
      if self._cache_enabled:
         current_hash = self._compute_url_hash()
         cache_key = f"{self._schema_cache_key}:{current_hash}"
         cache.delete(cache_key)

   def render_swagger_ui(self, request):
      openapi_json_url = reverse('djapy:openapi')
      absolute_openapi_json_url = request.build_absolute_uri(openapi_json_url)
      is_dark_mode = request.COOKIES.get("dark_mode", "false") == "true"
      return _render_cdn_template(request, ABS_TPL_PATH / 'swagger_cdn.html', {
         "swagger_settings": json.dumps({
            "url": absolute_openapi_json_url,
            "layout": "BaseLayout",
            "deepLinking": "true",
         }),
         "api": {
            "title": self.info.title,
            "site_name": self.info.site_name,
         },
         "dark_mode": is_dark_mode,
         "icons": icons,
         "active_icon": icons["light_mode" if is_dark_mode else "dark_mode"],
         "add_csrf": True,
         "csrf_token": request.COOKIES.get("csrftoken"),
      })

   def get_urls(self):
      return [
         path('openapi.json', self.get_openapi, name='openapi'),
         path('', self.render_swagger_ui, name='swagger')
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
