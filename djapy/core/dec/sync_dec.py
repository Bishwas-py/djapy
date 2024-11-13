import json
from functools import wraps

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse

from .base_dec import BaseDjapifyDecorator
from ..parser import RequestParser, ResponseParser
from ..view_func import WrappedViewT


class SyncDjapifyDecorator(BaseDjapifyDecorator):
   def __call__(self, view_func: WrappedViewT = None):
      if view_func is None:
         return lambda v: self.__call__(v)

      @wraps(view_func)
      def wrapped_view(request: HttpRequest, *args, **kwargs):
         self._prepare(view_func)

         if msg := self.check_access(request, view_func, *args, **kwargs):
            return msg

         try:
            response = HttpResponse(content_type="application/json")

            # Use sync request parser
            req_p = RequestParser(request, view_func, kwargs)
            data = req_p.parse_data()

            if view_func.djapy_resp_param:
               data[view_func.djapy_resp_param.name] = response

            content = view_func(request, *args, **data)

            # Use sync response parser
            res_p = ResponseParser(
               request=request,
               status=200 if not isinstance(content, tuple) else content[0],
               data=content if not isinstance(content, tuple) else content[1],
               schemas=view_func.schema,
               input_data=data
            )

            result = res_p.parse_data()
            if isinstance(content, tuple):
               response.status_code = content[0]
            response.content = json.dumps(result, cls=DjangoJSONEncoder)
            print(response.content)
            return response

         except Exception as exc:
            return self.handle_error(request, exc)

      self._set_common_attributes(wrapped_view, view_func)
      return wrapped_view
