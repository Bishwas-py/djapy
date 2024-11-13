import json
from functools import wraps
from django.http import HttpRequest, JsonResponse, HttpResponse

from .base_dec import BaseDjapifyDecorator
from ..defaults import DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
from ..parser import RequestDataParser, ResponseDataParser


class SyncDjapifyDecorator(BaseDjapifyDecorator):
   def __call__(self, view_func=None):
      if view_func is None:
         return lambda v: self.__call__(v)

      @wraps(view_func)
      def wrapped_view(request: HttpRequest, *args, **kwargs):
         self._prepare(view_func)

         if msg := self._check_access(request, *args, **kwargs):
            return msg

         try:
            response = HttpResponse(content_type="application/json")
            parser = RequestDataParser(request, view_func, kwargs)
            data = parser.parse_request_data()

            if view_func.in_response_param:
               data[view_func.in_response_param.name] = response

            content = view_func(request, *args, **data)
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
