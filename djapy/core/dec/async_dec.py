import asyncio
from functools import wraps
from django.http import HttpRequest, HttpResponse
from .base_dec import BaseDjapifyDecorator
from ..parser import RequestDataParser
from ..view_func import ViewFuncT


class AsyncDjapifyDecorator(BaseDjapifyDecorator):
   def __call__(self, view_func: ViewFuncT = None):
      if view_func is None:
         return lambda v: self.__call__(v)

      if not asyncio.iscoroutinefunction(view_func):
         raise ValueError(f"View function {view_func.__name__} must be async")

      @wraps(view_func)
      async def wrapped_view(request: HttpRequest, *args, **kwargs):
         self._prepare(view_func)

         if msg := self._check_access(request, *args, **kwargs):
            return msg

         try:
            response = HttpResponse(content_type="application/json")
            parser = RequestDataParser(request, view_func, kwargs)
            data = parser.parse_request_data()

            if view_func.djapy_resp_param:
               data[view_func.djapy_resp_param.name] = response

            content = await view_func(request, *args, **data)

            return self._get_response(
               response,
               content,
               view_func.schema,
               request,
               data
            )

         except Exception as exc:
            return self.handle_error(request, exc)

      self._set_common_attributes(wrapped_view, view_func)
      return wrapped_view
