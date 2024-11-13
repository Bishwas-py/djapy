from typing import Dict, Any, Union, Type, Optional
from abc import ABC, abstractmethod

from asgiref.sync import sync_to_async
from pydantic import create_model, BaseModel
from django.http import HttpRequest
from django.http.request import RawPostDataException

from djapy.schema import Schema
from .d_types import dyp
from .response import create_validation_error
from .labels import (
   REQUEST_INPUT_DATA_SCHEMA_NAME,
   RESPONSE_OUTPUT_SCHEMA_NAME,
   JSON_OUTPUT_PARSE_NAME,
   JSON_BODY_PARSE_NAME
)
from .view_func import WrappedViewT
from ..schema.schema import get_json_dict


class BaseParser(ABC):
   """Base parser with common functionality."""

   def __init__(self, request: HttpRequest):
      self.request = request
      self._context = {"request": request}
      self._body = None

   def _get_body(self) -> str:
      """Safely get request body."""
      if self._body is None:
         try:
            self._body = self.request.body.decode()
         except RawPostDataException:
            self._body = "{}"
      return self._body

   def _validate_schema(self, schema: Type[Schema], data: dict, extra_context: dict = None) -> dict:
      """Common schema validation logic."""
      if schema.is_empty():
         return {}

      context = {**self._context}
      if extra_context:
         context.update(extra_context)

      validated = schema.validate_via_request(data, context=context)
      return validated.__dict__


class RequestParser(BaseParser):
   """Base request parser with common request parsing logic."""

   def __init__(self, request: HttpRequest, view_func: WrappedViewT, view_kwargs: dict):
      super().__init__(request)
      self.view_func = view_func
      self.view_kwargs = view_kwargs
      self.schemas = view_func.djapy_inp_schema

   def parse_data(self) -> dict:
      """Parse and validate request data."""
      # Handle POST data first
      form = self._validate_schema(
         self.schemas["form"],
         dict(self.request.POST),
      )

      # Then handle JSON body
      body_data = {}
      if not self.schemas["data"].is_empty():
         body_str = self._get_body()
         if body_str:
            body_data = self._validate_schema(
               self.schemas["data"],
               get_json_dict(body_str),
            )

      # Finally handle query params
      query = self.schemas["query"].model_validate({
         **self.view_kwargs,
         **dict(self.request.GET)
      }, context=self._context)

      return {
         **query.__dict__,
         **body_data,
         **form,
      }


class ResponseParser(BaseParser):
   """Base response parser with common response parsing logic."""

   def __init__(
     self,
     request: HttpRequest,
     status: int,
     data: Any,
     schemas: dyp.schema,
     input_data: Optional[Dict[str, Any]] = None
   ):
      super().__init__(request)
      self.status = status
      self.data = data
      self.input_data = input_data

      if not isinstance(schemas, dict):
         raise create_validation_error("Response", "schemas", "invalid_type")
      self.schemas = schemas

   def _create_model(self) -> Type[BaseModel]:
      """Create response model from schema."""
      schema = self.schemas[self.status]
      return create_model(
         RESPONSE_OUTPUT_SCHEMA_NAME,
         **{JSON_OUTPUT_PARSE_NAME: (schema, ...)},
         __base__=Schema
      )

   def parse_data(self) -> Dict[str, Any]:
      """Parse and validate response data."""
      model = self._create_model()
      validated = model.model_validate(
         {JSON_OUTPUT_PARSE_NAME: self.data},
         context={**self._context, "input_data": self.input_data}
      )
      return validated.model_dump(mode="json", by_alias=True)[JSON_OUTPUT_PARSE_NAME]


class AsyncRequestParser(RequestParser):
   """Async request parser implementation."""

   async def parse_data(self) -> dict:
      """Async version of request data parsing."""
      return await sync_to_async(super().parse_data)()


class AsyncResponseParser(ResponseParser):
   """Async response parser implementation."""

   async def parse_data(self) -> Dict[str, Any]:
      """Async version of response data parsing."""
      return await sync_to_async(super().parse_data)()


def get_response_schema_dict(view_func: WrappedViewT) -> dyp.schema:
   """Get view function's response schema."""
   schema = view_func.__annotations__.get('return', None)
   return {200: schema} if not isinstance(schema, dict) else schema


# For backwards compatibility
RequestDataParser = RequestParser
ResponseDataParser = ResponseParser

__all__ = [
   'RequestDataParser',
   'ResponseDataParser',
   'AsyncRequestParser',
   'AsyncResponseParser',
   'get_response_schema_dict'
]
