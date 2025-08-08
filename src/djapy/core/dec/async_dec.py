import asyncio
import json
from functools import wraps
from asgiref.sync import sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse
from .base_dec import BaseDjapifyDecorator
from ..parser import AsyncRequestParser, AsyncResponseParser
from ..view_func import WrappedViewT


class AsyncDjapifyDecorator(BaseDjapifyDecorator):
   def __call__(self, view_func: WrappedViewT = None):
      if view_func is None:
         return lambda v: self.__call__(v)

      if not asyncio.iscoroutinefunction(view_func):
         raise ValueError(f"View function {view_func.__name__} must be async")

      @wraps(view_func)
      async def wrapped_view(request: HttpRequest, *args, **kwargs):
         self._prepare(view_func)

         if msg := await sync_to_async(self.check_access)(request, view_func, *args, **kwargs):
            return msg

         try:
            response = HttpResponse(content_type="application/json")

            # Use async request parser
            parser = AsyncRequestParser(request, view_func, kwargs)
            data = await parser.parse_data()

            if view_func.djapy_resp_param:
               data[view_func.djapy_resp_param.name] = response

            content = await view_func(request, *args, **data)

            # Use async response parser
            parser = AsyncResponseParser(
               request=request,
               status=200 if not isinstance(content, tuple) else content[0],
               data=content if not isinstance(content, tuple) else content[1],
               schemas=view_func.schema,
               input_data=data
            )

            result = await parser.parse_data()

            if isinstance(content, tuple):
               response.status_code = content[0]
            response.content = json.dumps(result, cls=DjangoJSONEncoder)
            return response

         except Exception as exc:
            return await sync_to_async(self.handle_error)(request, exc)

      self._set_common_attributes(wrapped_view, view_func)
      return wrapped_view
