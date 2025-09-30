import asyncio
import json
from functools import wraps
from asgiref.sync import sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse, JsonResponse
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
         # Lazy preparation - only prepare once
         if not hasattr(view_func, 'djapy_prepared'):
            self._prepare(view_func)
            view_func.djapy_prepared = True

         # Fast access check
         if msg := await sync_to_async(self.check_access)(request, view_func, *args, **kwargs):
            return msg

         try:
            # Use optimized async request parser
            parser = AsyncRequestParser(request, view_func, kwargs)
            data = await parser.parse_data()

            # Inject response if needed
            if view_func.djapy_resp_param:
               response = HttpResponse(content_type="application/json")
               data[view_func.djapy_resp_param.name] = response
            else:
               response = None

            # Execute async view function
            content = await view_func(request, *args, **data)

            # Determine status and data
            status = 200 if not isinstance(content, tuple) else content[0]
            response_data = content if not isinstance(content, tuple) else content[1]

            # Fast path: If already JsonResponse, return it
            if isinstance(content, JsonResponse):
               return content

            # Use optimized async response parser
            parser = AsyncResponseParser(
               request=request,
               status=status,
               data=response_data,
               schemas=view_func.schema,
               input_data=data
            )

            # Parse with mode='json' for JSON serialization
            result = await parser.parse_data()

            # Build response efficiently
            if response is None:
               response = HttpResponse(content_type="application/json")
            response.status_code = status
            # Use orjson if available for better performance, fallback to standard json
            try:
               import orjson
               response.content = orjson.dumps(result)
            except ImportError:
               response.content = json.dumps(result, cls=DjangoJSONEncoder)
            
            return response

         except Exception as exc:
            return await sync_to_async(self.handle_error)(request, exc)

      self._set_common_attributes(wrapped_view, view_func)
      return wrapped_view
