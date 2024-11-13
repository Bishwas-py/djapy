import asyncio
import json
from functools import wraps

from django.http import HttpRequest, JsonResponse, HttpResponse

from .base_dec import BaseDjapifyDecorator
from ..defaults import DEFAULT_METHOD_NOT_ALLOWED_MESSAGE
from ..parser import RequestDataParser, ResponseDataParser


class AsyncDjapifyDecorator(BaseDjapifyDecorator):
   def __call__(self, view_func=None):
      if view_func is None:
         return lambda v: self.__call__(v)

      if not asyncio.iscoroutinefunction(view_func):
         raise ValueError(f"View function {view_func.__name__} must be async")

      @wraps(view_func)
      async def wrapped_view(request: HttpRequest, *args, **kwargs):
         self._prepare_view(view_func)

         # Auth checks
         authentication_info = wrapped_view.auth_mechanism.authenticate(request, *args, **kwargs)
         if authentication_info:
            return JsonResponse(authentication_info[1], status=authentication_info[0])

         authorization_info = wrapped_view.auth_mechanism.authorize(request, *args, **kwargs)
         if authorization_info:
            return JsonResponse(authorization_info[1], status=authorization_info[0])

         # Method check
         if request.method not in wrapped_view.djapy_allowed_method:
            return JsonResponse(DEFAULT_METHOD_NOT_ALLOWED_MESSAGE, status=405)

         try:
            response = HttpResponse(content_type="application/json")
            request_parser = RequestDataParser(request, view_func, kwargs)
            input_data = request_parser.parse_request_data()

            if view_func.in_response_param:
               input_data[view_func.in_response_param.name] = response

            response_from_view = await view_func(request, *args, **input_data)

            if isinstance(response_from_view, HttpResponseBase):
               return response_from_view

            status_code, response_data = (response_from_view
                                          if isinstance(response_from_view, tuple)
                                          else (200, response_from_view))

            response_parser = ResponseDataParser(
               status_code, response_data, view_func.schema, request,
               input_data
            )
            parsed_data = response_parser.parse_response_data()

            response.status_code = status_code
            response.content = json.dumps(parsed_data)
            return response

         except Exception as e:
            return self._handle_error(request, e)

      self._set_common_attributes(wrapped_view, view_func)
      return wrapped_view
