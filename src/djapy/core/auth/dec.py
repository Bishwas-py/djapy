import inspect
import json
import asyncio
from functools import wraps
from typing import Dict, Callable, List, Type

from django.http import HttpRequest

from . import BaseAuthMechanism
from ..d_types import dyp
from ..defaults import DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
from djapy.core.auth import SessionAuth


def djapy_auth(auth: Type[BaseAuthMechanism] | BaseAuthMechanism | None = None,
               permissions: List[str] = None,
               msg=None) -> Callable:
   if permissions is None:
      permissions = []
   if not auth:
      auth = SessionAuth

   def decorator(view_func):
      @wraps(view_func)
      async def _wrapped_async_view(request: HttpRequest, *args, **kwargs):
         return await view_func(request, *args, **kwargs)

      @wraps(view_func)
      def _wrapped_sync_view(request: HttpRequest, *args, **kwargs):
         return view_func(request, *args, **kwargs)

      # Choose appropriate wrapper based on whether view is async
      wrapped = _wrapped_async_view if asyncio.iscoroutinefunction(view_func) else _wrapped_sync_view

      if auth and inspect.isclass(auth) and issubclass(auth, BaseAuthMechanism):
         wrapped.djapy_auth = auth(permissions)
      else:
         wrapped.djapy_auth = auth
      wrapped.djapy_auth.set_message_response(msg)

      return wrapped

   # Handle case where decorator is used without parentheses
   if inspect.isfunction(auth):
      return decorator(auth)

   return decorator


def djapy_method(
  allowed_method_or_list: dyp.methods,
  message_response: Dict[str, str] = None
) -> Callable:
   message_response = message_response or DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
   try:
      json.dumps(message_response)
   except TypeError as e:
      raise TypeError(f"Invalid message_response: {message_response}") from e

   def decorator(view_func):
      @wraps(view_func)
      async def _wrapped_async_view(request: HttpRequest, *args, **kwargs):
         if request.method not in allowed_method_or_list:
            view_func.djapy_message_response = message_response
         return await view_func(request, *args, **kwargs)

      @wraps(view_func)
      def _wrapped_sync_view(request: HttpRequest, *args, **kwargs):
         if request.method not in allowed_method_or_list:
            view_func.djapy_message_response = message_response
         return view_func(request, *args, **kwargs)

      # Choose appropriate wrapper based on whether view is async
      wrapped = _wrapped_async_view if asyncio.iscoroutinefunction(view_func) else _wrapped_sync_view

      # Set allowed methods
      if isinstance(allowed_method_or_list, str):
         wrapped.djapy_methods = [allowed_method_or_list]
      else:
         wrapped.djapy_methods = allowed_method_or_list

      return wrapped

   return decorator
