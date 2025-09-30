from typing import Dict, Any, Union, Type, Optional
from abc import ABC, abstractmethod
from functools import lru_cache
import json

from asgiref.sync import sync_to_async
from pydantic import create_model, BaseModel, TypeAdapter
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
   """Optimized request parser with Pydantic V2 performance features."""

   def __init__(self, request: HttpRequest, view_func: WrappedViewT, view_kwargs: dict):
      super().__init__(request)
      self.view_func = view_func
      self.view_kwargs = view_kwargs
      self.schemas = view_func.djapy_inp_schema
      self._type_adapters = self._get_type_adapters()

   @lru_cache(maxsize=1)
   def _get_type_adapters(self) -> dict:
      """Cache TypeAdapters for better performance."""
      return {
         "query": TypeAdapter(self.schemas["query"]),
         "data": TypeAdapter(self.schemas["data"]),
         "form": TypeAdapter(self.schemas["form"])
      }

   def parse_data(self) -> dict:
      """Parse and validate request data with optimizations."""
      # Handle POST data first
      form = self._validate_schema(
         self.schemas["form"],
         dict(self.request.POST),
      )

      # Then handle JSON body - use fast JSON parsing
      body_data = {}
      if not self.schemas["data"].is_empty():
         body_str = self._get_body()
         if body_str and body_str.strip():  # Check for non-empty
            try:
               # Fast path: use model_validate_json for better performance
               body_bytes = body_str.encode('utf-8')
               validated = self.schemas["data"].model_validate_json(
                  body_bytes,
                  context=self._context
               )
               body_data = validated.__dict__
            except Exception:
               # Fallback to dict parsing
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
   """Optimized response parser with multiple serialization modes."""

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
      self._model_cache = {}

   def _create_model(self) -> Type[BaseModel]:
      """Create response model from schema (cached)."""
      if self.status in self._model_cache:
         return self._model_cache[self.status]

      schema = self.schemas[self.status]
      model = create_model(
         RESPONSE_OUTPUT_SCHEMA_NAME,
         **{JSON_OUTPUT_PARSE_NAME: (schema, ...)},
         __base__=Schema
      )
      self._model_cache[self.status] = model
      return model

   def parse_data(self, mode: str = "json") -> Dict[str, Any]:
      """Parse and validate response data with specified serialization mode.
      
      Args:
          mode: Serialization mode - 'json' or 'python' (default: 'json')
      """
      # Fast path: Direct Pydantic model
      if isinstance(self.data, BaseModel):
         return self.data.model_dump(
            mode=mode,
            by_alias=True,
            exclude_unset=False,
            exclude_none=False
         )

      # Standard validation path
      model = self._create_model()
      validated = model.model_validate(
         {JSON_OUTPUT_PARSE_NAME: self.data},
         context={**self._context, "input_data": self.input_data}
      )
      return validated.model_dump(
         mode=mode,
         by_alias=True,
         exclude_unset=False
      )[JSON_OUTPUT_PARSE_NAME]


class AsyncRequestParser(RequestParser):
   """Async request parser implementation."""

   async def parse_data(self) -> dict:
      """Async version of request data parsing."""
      return await sync_to_async(super().parse_data)()


class AsyncResponseParser(ResponseParser):
   """Async response parser implementation."""

   async def parse_data(self) -> Dict[str, Any]:
      """Async version of response data parsing."""
      return await sync_to_async(super().parse_data)(mode="json")


def get_response_schema_dict(view_func: WrappedViewT) -> dyp.schema:
   """Get view function's response schema."""
   schema = view_func.__annotations__.get('return', None)
   return {200: schema} if not isinstance(schema, dict) else schema


__all__ = [
   'RequestParser',
   'ResponseParser',
   'AsyncRequestParser',
   'AsyncResponseParser',
   'get_response_schema_dict'
]
