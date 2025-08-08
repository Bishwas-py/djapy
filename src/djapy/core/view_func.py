from typing import TypeVar, Protocol, Callable, List, Any

from django.http import HttpRequest, HttpResponseBase
from djapy.core.d_types import dyp


class DjapyViewFunc(Protocol):
   """Protocol for Djapy decorated view functions."""
   djapy: bool
   openapi: bool
   openapi_tags: List[str]
   schema: dyp.schema
   djapy_message_response: Any
   djapy_inp_schema: dyp.inp_schema
   djapy_methods: dyp.methods
   djapy_auth: dyp.auth
   djapy_resp_param: dyp.resp_params
   djapy_req_params: dyp.params

   def __call__(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase: ...


ViewFuncT = TypeVar('ViewFuncT', bound=Callable[..., Any])
WrappedViewT = TypeVar('WrappedViewT', bound=DjapyViewFunc)
