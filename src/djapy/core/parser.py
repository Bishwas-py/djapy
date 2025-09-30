import inspect
import types
import typing
from multiprocessing.spawn import prepare
from typing import Dict, Any, Union, Type, Optional, get_origin, get_args, Generic
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
   RESPONSE_OUTPUT_SCHEMA_NAME,
   JSON_OUTPUT_PARSE_NAME,
   # REQUEST_INPUT_DATA_SCHEMA_NAME,
   # JSON_BODY_PARSE_NAME
)
from .type_check import schema_type
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


def is_typing_type(annotation) -> bool:
   """
   Reliably detect if an annotation is a typing type (List, Dict, Any, Union, etc.)
   """
   if annotation is None:
      return False

   if annotation in (Any, Union):
      return True

   if isinstance(annotation, types.UnionType):
      return True

   if isinstance(annotation, typing._GenericAlias):  # noqa
      return True

   return False


def prepare_schema(raw_schema: Dict[int, Type] | Any) -> Dict[int, Type]:
   """Prepare schema for response parsing."""
   if isinstance(raw_schema, dict):
      return raw_schema
   return {200: raw_schema}


def parse_tuple_annotation(annotation) -> Dict[int, Type]:
   """Parse return type annotations into status code -> schema mapping."""
   # First try prepare_schema for simple cases
   if not (get_origin(annotation) in (Union, tuple) or
           is_typing_type(annotation) or
           schema_type(annotation)):
      return prepare_schema(annotation)

   schemas = {}

   # Handle union of tuples case
   if get_origin(annotation) is Union:
      for tuple_type in get_args(annotation):
         schemas.update(parse_tuple_annotation(tuple_type))
      return schemas

   # Handle single tuple case
   if get_origin(annotation) is tuple:
      args = get_args(annotation)
      if len(args) != 2:
         raise ValueError(
            "Tuple return types must have "
            "exactly 2 elements: (status_code, schema)"
         )

      status_code = args[0]
      if not isinstance(status_code, int):
         if hasattr(status_code, "__supertype__") and isinstance(status_code.__supertype__, int):
            status_code = status_code.__supertype__
         else:
            raise ValueError(f"First tuple element must be an integer status code, got {status_code}")

      schemas[status_code] = args[1]
      return schemas

   # Handle typing types and schema types
   if is_typing_type(annotation) or schema_type(annotation):
      return prepare_schema(annotation)

   return schemas


def get_response_schema_dict(view_func) -> Dict[int, Type]:
   """Get response schema from view function return annotation.
   Handles both dictionary and tuple formats."""
   schema = view_func.__annotations__.get('return')

   if schema is None:
      return {}

   if isinstance(schema, dict):
      return schema

   try:
      return parse_tuple_annotation(schema)
   except (ValueError, AttributeError) as e:
      raise ValueError(
         f"Invalid return type annotation. Must be either a dict "
         f"mapping status codes to schemas, or a Tuple/Union of "
         f"Tuples. Error: {str(e)}")


__all__ = [
   'RequestParser',
   'ResponseParser',
   'AsyncRequestParser',
   'AsyncResponseParser',
   'get_response_schema_dict'
]
