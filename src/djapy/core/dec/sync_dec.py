import json
from functools import wraps

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse, JsonResponse

from .base_dec import BaseDjapifyDecorator
from ..parser import RequestParser, ResponseParser
from ..view_func import WrappedViewT


class SyncDjapifyDecorator(BaseDjapifyDecorator):
   def __call__(self, view_func: WrappedViewT = None):
      if view_func is None:
         return lambda v: self.__call__(v)

      @wraps(view_func)
      def wrapped_view(request: HttpRequest, *args, **kwargs):
         # Lazy preparation - only prepare once
         if not hasattr(view_func, 'djapy_prepared'):
            self._prepare(view_func)
            view_func.djapy_prepared = True

         # Fast access check
         if msg := self.check_access(request, view_func, *args, **kwargs):
            return msg

         try:
            # Use optimized request parser with caching
            req_p = RequestParser(request, view_func, kwargs)
            data = req_p.parse_data()

            # Inject response if needed
            if view_func.djapy_resp_param:
               response = HttpResponse(content_type="application/json")
               data[view_func.djapy_resp_param.name] = response
            else:
               response = None

            # Execute view function
            content = view_func(request, *args, **data)

            # Determine status and data
            status = 200 if not isinstance(content, tuple) else content[0]
            response_data = content if not isinstance(content, tuple) else content[1]

            # Fast path: If already JsonResponse, return it
            if isinstance(content, JsonResponse):
               return content

            # Use optimized response parser
            res_p = ResponseParser(
               request=request,
               status=status,
               data=response_data,
               schemas=view_func.schema,
               input_data=data
            )

            # Parse with mode='json' for JSON serialization
            result = res_p.parse_data(mode='json')
            
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
            return self.handle_error(request, exc)

      self._set_common_attributes(wrapped_view, view_func)
      return wrapped_view
