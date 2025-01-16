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
   URL_PARAM_PATTERN = re.compile(r'[<](?:(?P<type>\w+?):)?(?P<name>\w+)[>]')

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
      self.export_security_schemes.update(self.view_func.auth_mechanism.schema())  # AuthMechanism.schema

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
      for schema in (self.view_func.input_schema["data"], self.view_func.input_schema["form"]):
         if single_schema := schema.single():
            schema = single_schema[1]

         prepared_schema = schema.model_json_schema(ref_template=REF_MODAL_TEMPLATE)
         if not prepared_schema.get("properties"):
            continue

         if "$defs" in prepared_schema:
            self.export_components.update(prepared_schema.pop("$defs"))

         content_type = schema.cvar_c_type
         if not self.request_body.get("content"):
            self.request_body["content"] = {}

         self.request_body["content"][content_type] = {"schema": prepared_schema}

   @staticmethod
   def make_parameters(name, schema, required, in_="query"):
      return {
         "name": name,
         "in": in_,
         "required": required,
         "schema": schema
      }

   def set_parameters(self):
      # Combine parameter setting logic from parent and required params
      url_params = set()

      # Process parent URL patterns first
      for url_pattern in self.parent_url_pattern + [self.url_pattern]:
         if match := self.URL_PARAM_PATTERN.search(str(url_pattern.pattern)):
            _type, name = match.groups()
            if name not in self.parameters_keys:
               schema = basic_query_schema(_type)
               self.parameters_keys.append(name)
               self.parameters.append(self.make_parameters(name, schema, True, "path"))
               url_params.add(name)

      # Process query parameters
      query_schema = self.view_func.input_schema["query"].model_json_schema(ref_template=REF_MODAL_TEMPLATE)
      if query_schema.get("properties"):
         for name, schema in query_schema["properties"].items():
            if name not in self.parameters_keys:
               required_ = name in query_schema.get("required", [])
               is_url_param = name in url_params
               self.parameters_keys.append(name)
               self.parameters.append(self.make_parameters(
                  name=name,
                  schema=schema,
                  required=required_,
                  in_="path" if is_url_param else "query"
               ))

   def set_path(self):
      paths = [self.format_pattern(p) for p in (self.parent_url_pattern or []) + [self.url_pattern]]
      url_path_string = ''.join(paths)
      self.path = f"/{url_path_string.lstrip('/')}"

   @staticmethod
   def format_pattern(url_pattern: URLPattern) -> str:
      pattern = r'[<](?:(?P<type>\w+?):)?(?P<variable>\w+)[>]'
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
         description = (isinstance(schema, Schema)
                        and schema.Info.cvar_describe
                        and schema.Info.cvar_describe.get(status)) \
                       or self.make_description_from_status(status)

         response_model = create_model(
            'openapi_response_model',
            response=(schema, ...),
            __base__=Schema
         )

         prepared_schema = response_model.model_json_schema(
            ref_template=REF_MODAL_TEMPLATE,
            mode='serialization'
         )

         if "$defs" in prepared_schema:
            self.export_components.update(prepared_schema.pop("$defs"))

         self.responses[str(status)] = {
            "description": description,
            "content": {
               "application/json": {
                  "schema": prepared_schema['properties']['response']
               }
            }
         }

   def dict(self):

      return {
         method.lower(): {
            "summary": self.summary,
            "description": self.explanation,
            "operationId": self.operation_id + f".{method.lower()}",
            "responses": self.responses,
            "parameters": self.parameters,
            "requestBody": self.request_body,
            "tags": self.tags,
            "security": self.security
         } for method in self.methods
      }
