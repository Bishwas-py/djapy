import json
from functools import wraps

from django.http import HttpRequest, JsonResponse, HttpResponse, HttpResponseBase

from .base_dec import BaseDjapifyDecorator
from ..defaults import DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
from ..parser import RequestDataParser, ResponseDataParser


class SyncDjapifyDecorator(BaseDjapifyDecorator):
   def __call__(self, view_func=None):
      if view_func is None:
         return lambda v: self.__call__(v)

      @wraps(view_func)
      def wrapped_view(request: HttpRequest, *args, **kwargs):
         self._prepare_view(wrapped_view)

         if msg := self._is_blocked(request, *args, **kwargs):
            return msg

         try:
            response = HttpResponse(content_type="application/json")
            request_parser = RequestDataParser(request, view_func, kwargs)
            input_data = request_parser.parse_request_data()

            if view_func.in_response_param:
               input_data[view_func.in_response_param.name] = response

            response_from_view = view_func(request, *args, **input_data)
            return self._parsed_response(
               response,
               response_from_view,
               view_func.schema,
               request, input_data
            )
         except Exception as e:
            return self.handle_error(request, e)

      self._set_common_attributes(wrapped_view, view_func)
      return wrapped_view
