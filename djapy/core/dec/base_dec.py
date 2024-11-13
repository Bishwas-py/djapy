import inspect
import importlib
import json
import logging
from typing import Callable, Dict, Type, List, Optional, Union, Any, TypeVar, Protocol

from django.http import HttpRequest, JsonResponse, HttpResponseBase
from pydantic import ValidationError, create_model

from djapy.core.auth import BaseAuthMechanism, base_auth_obj
from djapy.core.d_types import dyp
from djapy.core.defaults import (
   DEFAULT_MESSAGE_ERROR,
   DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
)
from djapy.core.parser import get_response_schema_dict, ResponseDataParser
from djapy.core.response import create_json_from_validation_error
from djapy.core.type_check import (
   is_param_query_type,
   is_data_type
)
from djapy.core.labels import (
   REQUEST_INPUT_DATA_SCHEMA_NAME,
   REQUEST_INPUT_QUERY_SCHEMA_NAME,
   REQUEST_INPUT_FORM_SCHEMA_NAME, DJAPY_ALLOWED_METHOD, DJAPY_AUTH
)
from djapy.core.view_func import WrappedViewT, ViewFuncT
from djapy.schema.schema import Schema, Form, QueryMapperSchema

ERROR_HANDLER_MODULE = "djapy_ext.errorhandler"
ERROR_HANDLER_PREFIX = "handle_"


class BaseDjapifyDecorator:
   def __init__(
     self,
     view_func: WrappedViewT,
     method: dyp.methods = "GET",
     openapi: bool = True,
     tags: List[str] = None,
     auth: dyp.auth = base_auth_obj
   ):
      self.view_func: WrappedViewT = view_func
      self.method = method
      self.openapi = openapi
      self.tags = tags
      self.auth = auth
      self.app_auth: dyp.auth = None
      self.handlers = self._get_handlers()

   @staticmethod
   def _get_handlers() -> List[Callable]:
      handlers = []
      try:
         handler = importlib.import_module(ERROR_HANDLER_MODULE)
         for name in dir(handler):
            if name.startswith(ERROR_HANDLER_PREFIX):
               handlers.append(getattr(handler, name))
      except ImportError:
         pass
      return handlers

   @staticmethod
   def check_access(request: HttpRequest, w: WrappedViewT, *args, **kwargs) -> Optional[JsonResponse]:
      methods = w.djapy_methods
      is_single = methods and isinstance(methods, str) and request.method != methods
      is_multiple = methods and request.method not in methods
      if is_single or is_multiple:
         return JsonResponse(DEFAULT_METHOD_NOT_ALLOWED_MESSAGE, status=405)
      if not w.djapy_auth:
         return None
      if r := w.djapy_auth.authenticate(request, *args, **kwargs):
         return JsonResponse(r[1], status=r[0])

   @staticmethod
   def _get_tuple(param: inspect.Parameter, annotation: Any = None) -> tuple:
      """Get tuple for pydantic model creation"""
      if annotation is None:
         annotation = param.annotation
      return (annotation, ...) if param.default is inspect.Parameter.empty else (annotation, param.default)

   def _add_query(self, param: inspect.Parameter, queries: Dict) -> None:
      """Add query parameter to schema dictionary"""
      if param.annotation is inspect.Parameter.empty:
         raise TypeError(
            f"Parameter `{param.name}` should have a type annotation, because it's required. e.g. "
            f"`def view_func({param.name}: str):`"
         )
      queries[param.name] = self._get_tuple(param)

   def _add_content(self, param: inspect.Parameter, forms: Dict,
                    data: Dict, data_type: Any) -> None:
      """Add content type to appropriate schema"""
      annotation, default = self._get_tuple(param, data_type)
      has_type = hasattr(annotation, 'cvar_c_type')

      if has_type:
         if annotation.cvar_c_type == "application/x-www-form-urlencoded":
            forms[param.name] = (annotation, default)
         elif annotation.cvar_c_type == "application/json":
            data[param.name] = (annotation, default)
      else:
         data[param.name] = (annotation, default)

   def _prepare(self, w: WrappedViewT) -> None:
      """Prepare view function attributes"""
      w.djapy_req_params = self._get_params(w)
      w.djapy_resp_param = self._get_response_param(w.djapy_req_params)
      module = self._get_module(w)
      self.app_auth = getattr(module, "AUTH_MECHANISM", None)

   @staticmethod
   def _get_params(view_func: Callable) -> dyp.params:
      """Get required parameters from signature"""
      signature = inspect.signature(view_func)
      return [
         param for i, (_, param) in enumerate(signature.parameters.items())
         if param.kind == param.POSITIONAL_OR_KEYWORD and i != 0
      ]

   @staticmethod
   def _get_response_param(params: dyp.resp_params) -> dyp.resp_params:
      """Get response parameter if exists"""
      for param in params:
         if inspect.isclass(param.annotation) and issubclass(param.annotation, HttpResponseBase):
            return param
      return None

   @staticmethod
   def _get_module(view_func: Callable):
      """Get view function module"""
      return inspect.getmodule(view_func)

   def _get_auth(self, view_func: ViewFuncT) -> BaseAuthMechanism:
      """Get auth mechanism for view"""
      auth = getattr(view_func, DJAPY_AUTH, None) or self.auth

      if auth == base_auth_obj and self.app_auth:
         handler = self.app_auth
      elif auth is None:
         return base_auth_obj
      else:
         handler = auth

      if inspect.isclass(handler) and issubclass(handler, BaseAuthMechanism):
         handler = handler()

      if not isinstance(handler, BaseAuthMechanism):
         raise TypeError(
            f"auth should be a class that inherits from BaseAuthMechanism, not {handler.__name__} or {type(handler)}"
         )

      return handler

   def handle_error(self, request: HttpRequest, exc: Exception) -> JsonResponse:
      """Handle errors uniformly"""
      for handler in self.handlers:
         try:
            signature = inspect.signature(handler)
            exc_param = signature.parameters.get('exception')
            if exc.__class__ == exc_param.annotation:
               result = handler(request, exc)
               if isinstance(result, JsonResponse):
                  return result
               if isinstance(result, tuple):
                  status, response = result
               else:
                  status, response = 400, result
               if isinstance(response, dict):
                  return JsonResponse(response, status=status)
         except Exception as e:
            logging.exception(f"Error in custom handler: {e}")

      if isinstance(exc, ValidationError):
         return JsonResponse(
            create_json_from_validation_error(exc),
            status=400,
            safe=False
         )

      logging.exception(exc)
      return JsonResponse(DEFAULT_MESSAGE_ERROR, status=500)

   def _get_schemas(self, w: WrappedViewT) -> tuple[
      Any, dict[str, Type[Schema | Form | QueryMapperSchema]]]:
      """Get request and response schemas"""
      schemas = get_response_schema_dict(w)
      queries = getattr(w, 'extra_query_dict', {}) or {}

      query = {}
      data = {}
      form = {}

      for param in w.djapy_req_params:
         if is_param_query_type(param):
            self._add_query(param, query)
         elif data_type := is_data_type(param):
            self._add_content(param, form, data, data_type)

      djapy_inp_schema = {
         "query": create_model(
            REQUEST_INPUT_QUERY_SCHEMA_NAME,
            **query,
            **queries,
            __base__=QueryMapperSchema
         ),
         "data": create_model(
            REQUEST_INPUT_DATA_SCHEMA_NAME,
            **data,
            __base__=Schema
         ),
         "form": create_model(
            REQUEST_INPUT_FORM_SCHEMA_NAME,
            **form,
            __base__=Form
         )
      }

      if hasattr(w, 'response_wrapper'):
         status, wrapper = w.response_wrapper
         if status in schemas:
            schemas[status] = wrapper[schemas[status]]

      return schemas, djapy_inp_schema

   def _set_common_attributes(self, wf: WrappedViewT, vf: ViewFuncT) -> None:
      """Set common view attributes"""
      self._prepare(vf)
      schemas, djapy_inp_schema = self._get_schemas(vf)

      wf.djapy = True
      wf.openapi = self.openapi
      wf.openapi_tags = self.tags or getattr(self._get_module(vf), 'TAGS', [])
      vf.schema = wf.schema = schemas
      wf.djapy_message_response = getattr(vf, 'djapy_message_response', None)
      vf.djapy_inp_schema = wf.djapy_inp_schema = djapy_inp_schema

      # Set auth mechanism
      wf.djapy_auth = self._get_auth(vf)
      vf.djapy_auth = wf.djapy_auth

      # Set allowed methods
      wf.djapy_methods = [self.method] if isinstance(self.method, str) else self.method
      vf.djapy_methods = wf.djapy_methods
