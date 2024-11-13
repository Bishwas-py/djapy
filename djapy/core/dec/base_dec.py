import inspect
import json
import types
from functools import wraps
from typing import Callable, Dict, Type, List, TypeVar, Optional, Any, Union

from django.http import HttpRequest, JsonResponse, HttpResponse, HttpResponseBase
from pydantic import ValidationError, create_model

from djapy.core.auth import BaseAuthMechanism, base_auth_obj
from djapy.core.defaults import ALLOW_METHODS_LITERAL, DEFAULT_METHOD_NOT_ALLOWED_MESSAGE, DEFAULT_MESSAGE_ERROR
from djapy.pagination.base_pagination import BasePagination
from djapy.core.parser import ResponseDataParser, RequestDataParser, get_response_schema_dict
from djapy.core.labels import REQUEST_INPUT_DATA_SCHEMA_NAME, REQUEST_INPUT_QUERY_SCHEMA_NAME
from djapy.core.response import create_json_from_validation_error
from djapy.schema import Schema

import logging

T = TypeVar('T')


class BaseDjapifyDecorator:
   """Base class for both sync and async djapify decorators"""

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

   def _prepare_view(self, view_func: Callable) -> None:
      """Prepare view function with common attributes"""
      view_func.required_params = self._get_required_params(view_func)
      view_func.in_response_param = None
      view_func.in_response_param = self._get_in_response_param(view_func.required_params)
      view_func_module = self._get_view_module(view_func)
      self.in_app_auth_mechanism = getattr(view_func_module, 'AUTH_MECHANISM', None)

   def _get_required_params(self, view_func: Callable) -> List[inspect.Parameter]:
      """Extract required parameters from a function signature, skipping the first one."""
      signature = inspect.signature(view_func)
      return [param for index, param in enumerate(signature.parameters.items())
              if param[1].kind == param[1].POSITIONAL_OR_KEYWORD and index != 0]

   def _get_in_response_param(self, required_params: List[inspect.Parameter]) -> Optional[inspect.Parameter]:
      """Get response parameter if it exists"""
      for param in required_params:
         if inspect.isclass(param.annotation) and issubclass(param.annotation, HttpResponseBase):
            return param
      return None

   def _get_view_module(self, view_func: Callable):
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
            f"auth should be a class that inherits from BaseAuthMechanism, not {wrapped_auth.__name__} or {type(wrapped_auth)}")

      return wrapped_auth

   def _get_schemas(self, view_func: Callable, extra_query_dict: Dict = None) -> Dict:
      """Get request and response schemas"""
      schema_dict_returned = get_response_schema_dict(view_func)

      extra_query_dict = getattr(view_func, 'extra_query_dict', {})
      response_wrapper = getattr(view_func, 'response_wrapper', None)

      if response_wrapper:
         status, wrapper_schema = response_wrapper
         if status in schema_dict_returned:
            schema_dict_returned[status] = wrapper_schema[schema_dict_returned[status]]

      return schema_dict_returned

   def _handle_error(self, request: HttpRequest, exception: Exception) -> Optional[JsonResponse]:
      """Handle errors uniformly for both sync and async views"""
      if isinstance(exception, ValidationError):
         return JsonResponse(create_json_from_validation_error(exception), status=400)

      logging.exception(exception)
      return JsonResponse(DEFAULT_MESSAGE_ERROR, status=500)

   def _set_common_attributes(self, wrapped_view: Callable, view_func: Callable) -> None:
      """Set common attributes on the wrapped view"""
      wrapped_view.djapy = True
      wrapped_view.openapi = self.openapi
      wrapped_view.openapi_tags = self.tags or getattr(self._get_view_module(view_func), 'TAGS', [])

      schema_dict = self._get_schemas(view_func, {})
      view_func.schema = wrapped_view.schema = schema_dict

      wrapped_view.djapy_message_response = getattr(view_func, 'djapy_message_response', None)
      wrapped_view.auth_mechanism = self._get_auth(view_func)

      if not getattr(wrapped_view, 'djapy_allowed_method', None):
         if isinstance(self.allowed_method, str):
            wrapped_view.djapy_allowed_method = [self.allowed_method]
         else:
            wrapped_view.djapy_allowed_method = self.allowed_method
