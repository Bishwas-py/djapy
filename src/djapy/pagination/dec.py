import types
import asyncio
from functools import wraps
from typing import Type, Callable

from django.http import HttpRequest

from djapy.core.view_func import ViewFuncT
from djapy.pagination import BasePagination, OffsetLimitPagination


def paginate(pagination_class: Type[BasePagination] | None = None) -> Callable:
   """
   Enhanced pagination decorator that consumes its own parameters.
   
   Pagination parameters (offset, limit, page_number, etc.) are:
   1. Added to the view's query schema
   2. Validated by djapy
   3. Stored in input_data context
   4. Filtered out before calling the view function
   
   This means view functions don't need **kwargs for pagination!
   """
   if pagination_class is None:
      pagination_class = OffsetLimitPagination

   def decorator(view_func: ViewFuncT):
      # Check if the view is async
      is_async = asyncio.iscoroutinefunction(view_func)
      
      # Get pagination parameter names to filter them out before calling view
      pagination_param_names = {name for name, _, _ in pagination_class.query}

      if is_async:
         @wraps(view_func)
         async def _wrapped_view(request: HttpRequest, *args, **kwargs):
            # Filter out pagination parameters before passing to view
            view_kwargs = {k: v for k, v in kwargs.items() if k not in pagination_param_names}
            return await view_func(request, *args, **view_kwargs)
      else:
         @wraps(view_func)
         def _wrapped_view(request: HttpRequest, *args, **kwargs):
            # Filter out pagination parameters before passing to view
            view_kwargs = {k: v for k, v in kwargs.items() if k not in pagination_param_names}
            return view_func(request, *args, **view_kwargs)

      extra_query_dict = {}
      if pagination_class:
         if not issubclass(pagination_class, BasePagination):
            pagination_type_invalid_msg = (f"pagination_class should be a class that inherits from BasePagination, "
                                           f"not {pagination_class.__name__} or {type(pagination_class)}")
            raise TypeError(pagination_type_invalid_msg)

         extra_query_dict = {
            name: (type_name_, default)
            for name, type_name_, default in pagination_class.query
         }

      _wrapped_view.response_wrapper = (200, pagination_class.response)
      _wrapped_view.extra_query_dict = extra_query_dict
      _wrapped_view.pagination_class = pagination_class  # Store for response validator

      # Preserve the async nature of the view
      if is_async:
         _wrapped_view.__is_async__ = True

      return _wrapped_view

   if pagination_class and isinstance(pagination_class, types.FunctionType):
      view_func = pagination_class
      pagination_class = OffsetLimitPagination
      return decorator(view_func)

   return decorator
