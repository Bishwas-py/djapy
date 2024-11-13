import inspect
import importlib
import json
import logging
from typing import Callable, Dict, Type, List, Optional, Union, Any

from django.http import HttpRequest, JsonResponse, HttpResponseBase
from pydantic import ValidationError, create_model

from djapy.core.auth import BaseAuthMechanism, base_auth_obj
from djapy.core.defaults import (
   ALLOW_METHODS_LITERAL,
   DEFAULT_MESSAGE_ERROR, ALLOWED_METHODS, DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
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
   REQUEST_INPUT_FORM_SCHEMA_NAME
)
from djapy.schema.schema import Schema, Form, QueryMapperSchema

ERROR_HANDLER_MODULE = "djapy_ext.errorhandler"
ERROR_HANDLER_PREFIX = "handle_"


class BaseDjapifyDecorator:
   def __init__(self,
                view_func: Optional[Callable] = None,
                allowed_method: Union[ALLOW_METHODS_LITERAL, List[ALLOW_METHODS_LITERAL]] = "GET",
                openapi: bool = True,
                tags: List[str] = None,
                auth: Optional[Union[Type[BaseAuthMechanism], BaseAuthMechanism]] = base_auth_obj):
      self.view_func = view_func
      self.allowed_method = allowed_method
      self.openapi = openapi
      self.tags = tags
      self.auth = auth
      self.in_app_auth_mechanism = None
      self._errorhandler_functions = self._initialize_error_handlers()

   @staticmethod
   def _initialize_error_handlers() -> List[Callable]:
      handlers = []
      try:
         error_handler = importlib.import_module(ERROR_HANDLER_MODULE)
         for name in dir(error_handler):
            if name.startswith(ERROR_HANDLER_PREFIX):
               handlers.append(getattr(error_handler, name))
      except ImportError:
         pass
      return handlers

   def _is_blocked(self, request: HttpRequest, *args, **kwargs):
      auth_mechanism: BaseAuthMechanism = getattr(self.view_func, "auth_mechanism", None)
      djapy_allowed_method: ALLOWED_METHODS = getattr(self.view_func, "djapy_allowed_method", None)

      if not auth_mechanism:
         auth_mechanism = self.auth

      auth_tuple = auth_mechanism.authenticate(request, *args, **kwargs)
      if auth_tuple:
         return JsonResponse(auth_tuple[1], status=auth_tuple[0])

      single_method = isinstance(djapy_allowed_method, str) and request.method != djapy_allowed_method
      multiple_methods = request.method not in djapy_allowed_method

      if djapy_allowed_method and (single_method or multiple_methods):
         return JsonResponse(DEFAULT_METHOD_NOT_ALLOWED_MESSAGE, status=405)

   @staticmethod
   def _parsed_response(
     response: HttpResponseBase,
     response_from_view: Any,
     schema: Dict[int, Union[Type[Schema], Type[Form]]],
     request: HttpRequest,
     input_data: Dict[str, Any]
   ) -> HttpResponseBase:
      if isinstance(response_from_view, HttpResponseBase):
         return response_from_view

      status_code, response_data = (
         response_from_view if isinstance(response_from_view, tuple)
         else (200, response_from_view)
      )

      response_parser = ResponseDataParser(
         status_code,
         response_data,
         schema,
         request,
         input_data
      )
      parsed_data = response_parser.parse_response_data()

      response.status_code = status_code
      response.content = json.dumps(parsed_data)
      return response

   @staticmethod
   def _get_passable_tuple(param: inspect.Parameter, annotation: Any = None) -> tuple:
      """Get a passable tuple for pydantic model creation"""
      if annotation is None:
         annotation = param.annotation
      return (annotation, ...) if param.default is inspect.Parameter.empty else (annotation, param.default)

   def _add_query_schema(self, param: inspect.Parameter, query_schema_dict: Dict) -> None:
      """Add a query parameter to the schema dictionary"""
      if param.annotation is inspect.Parameter.empty:
         raise TypeError(
            f"Parameter `{param.name}` should have a type annotation, because it's required. e.g. "
            f"`def view_func({param.name}: str):`"
         )
      query_schema_dict[param.name] = self._get_passable_tuple(param)

   def _add_content_type_schema(self, param: inspect.Parameter, form_schema_dict: Dict,
                                data_schema_dict: Dict, data_type: Any) -> None:
      """Add content type schema to appropriate dictionary"""
      annotation, default = self._get_passable_tuple(param, data_type)
      has_content_type = hasattr(annotation, 'cvar_c_type')

      if has_content_type:
         if annotation.cvar_c_type == "application/x-www-form-urlencoded":
            form_schema_dict[param.name] = (annotation, default)
         elif annotation.cvar_c_type == "application/json":
            data_schema_dict[param.name] = (annotation, default)
      else:
         data_schema_dict[param.name] = (annotation, default)

   def _prepare_view(self, view_func: Callable) -> None:
      """Prepare view function with common attributes"""
      view_func.required_params = self._get_required_params(view_func)
      view_func.in_response_param = self._get_in_response_param(view_func.required_params)
      view_func_module = self._get_view_module(view_func)
      self.in_app_auth_mechanism = getattr(view_func_module, 'AUTH_MECHANISM', None)

   @staticmethod
   def _get_required_params(view_func: Callable) -> List[inspect.Parameter]:
      """Extract required parameters from function signature"""
      signature = inspect.signature(view_func)
      return [
         param for i, (_, param) in enumerate(signature.parameters.items())
         if param.kind == param.POSITIONAL_OR_KEYWORD and i != 0
      ]

   @staticmethod
   def _get_in_response_param(required_params: List[inspect.Parameter]) -> Optional[inspect.Parameter]:
      """Get response parameter if it exists"""
      for param in required_params:
         if inspect.isclass(param.annotation) and issubclass(param.annotation, HttpResponseBase):
            return param
      return None

   @staticmethod
   def _get_view_module(view_func: Callable):
      """Get the module of the view function"""
      return inspect.getmodule(view_func)

   def _get_auth(self, view_func: Callable) -> BaseAuthMechanism:
      """Set the auth mechanism for the view function"""
      auth = getattr(view_func, 'auth_mechanism', None) or self.auth

      if auth == base_auth_obj and self.in_app_auth_mechanism:
         wrapped_auth = self.in_app_auth_mechanism
      elif auth is None:
         return base_auth_obj
      else:
         wrapped_auth = auth

      if inspect.isclass(wrapped_auth) and issubclass(wrapped_auth, BaseAuthMechanism):
         wrapped_auth = wrapped_auth()

      if not isinstance(wrapped_auth, BaseAuthMechanism):
         raise TypeError(
            f"auth should be a class that inherits from BaseAuthMechanism, not {wrapped_auth.__name__} or {type(wrapped_auth)}"
         )

      return wrapped_auth

   def _get_schemas(self, view_func: Callable) -> tuple[Any, dict[str, Type[Schema | Form | QueryMapperSchema]]]:
      """Get request and response schemas"""
      schema_dict_returned = get_response_schema_dict(view_func)

      # Create schema dictionaries
      query_schema_dict: Dict = {}
      data_schema_dict: Dict = {}
      form_schema_dict: Dict = {}

      # Process required parameters
      for param in view_func.required_params:
         if is_param_query_type(param):
            self._add_query_schema(param, query_schema_dict)
         elif data_type := is_data_type(param):
            self._add_content_type_schema(param, form_schema_dict, data_schema_dict, data_type)

      # Create input schemas
      input_schema = {
         "query": create_model(REQUEST_INPUT_QUERY_SCHEMA_NAME, **query_schema_dict, __base__=QueryMapperSchema),
         "data": create_model(REQUEST_INPUT_DATA_SCHEMA_NAME, **data_schema_dict, __base__=Schema),
         "form": create_model(REQUEST_INPUT_FORM_SCHEMA_NAME, **form_schema_dict, __base__=Form)
      }

      # Handle response wrapper
      if hasattr(view_func, 'response_wrapper'):
         status, wrapper_schema = view_func.response_wrapper
         if status in schema_dict_returned:
            schema_dict_returned[status] = wrapper_schema[schema_dict_returned[status]]

      return schema_dict_returned, input_schema

   def handle_error(self, request: HttpRequest, exception: Exception) -> JsonResponse:
      """Handle errors uniformly"""
      # Try custom error handlers first
      for handler in self._errorhandler_functions:
         try:
            signature = inspect.signature(handler)
            exception_param = signature.parameters.get('exception')
            if exception.__class__ == exception_param.annotation:
               result = handler(request, exception)
               if isinstance(result, JsonResponse):
                  return result
               if isinstance(result, tuple):
                  status, response = result
               else:
                  status, response = 400, result
               if isinstance(response, dict):
                  return JsonResponse(response, status=status)
         except Exception as e:
            logging.exception(f"Error in custom error handler: {e}")

      # Handle ValidationError
      if isinstance(exception, ValidationError):
         return JsonResponse(
            create_json_from_validation_error(exception),
            status=400,
            safe=False
         )

      # Log and return default error
      logging.exception(exception)
      return JsonResponse(DEFAULT_MESSAGE_ERROR, status=500)

   def _set_common_attributes(self, wrapped_view: Callable, view_func: Callable) -> None:
      """Set common attributes on the wrapped view"""
      # Prepare view and get schemas
      self._prepare_view(view_func)
      schema_dict, input_schema = self._get_schemas(view_func)

      # Set attributes
      wrapped_view.djapy = True
      wrapped_view.openapi = self.openapi
      wrapped_view.openapi_tags = self.tags or getattr(self._get_view_module(view_func), 'TAGS', [])
      view_func.schema = wrapped_view.schema = schema_dict
      view_func.input_schema = wrapped_view.input_schema = input_schema
      wrapped_view.djapy_message_response = getattr(view_func, 'djapy_message_response', None)
      wrapped_view.auth_mechanism = self._get_auth(view_func)

      if not getattr(wrapped_view, 'djapy_allowed_method', None):
         wrapped_view.djapy_allowed_method = (
            [self.allowed_method] if isinstance(self.allowed_method, str)
            else self.allowed_method
         )
