from typing import Dict, Any, Union, Type

from pydantic import create_model, BaseModel, Json
from django.http import HttpRequest

from djapy.schema import Schema
from .response import create_validation_error
from .labels import REQUEST_INPUT_DATA_SCHEMA_NAME, RESPONSE_OUTPUT_SCHEMA_NAME, JSON_OUTPUT_PARSE_NAME, \
   JSON_BODY_PARSE_NAME

__all__ = ['RequestDataParser', 'ResponseDataParser', 'get_response_schema_dict']

from ..schema.schema import json_modal_schema, get_json_dict


class RequestDataParser:
   def __init__(self, request: HttpRequest, view_func, view_kwargs):
      self.view_func = view_func
      self.view_kwargs = view_kwargs
      self.request = request
      self.query_data = {}
      self.line_kwargs = {}
      self.data = {}
      self.form = {}
      self.files = {}

   def parse_request_data(self):
      """
      Parse the request data and validate it with the data model.
      """
      context = {"request": self.request}
      data_schema = self.view_func.input_schema["data"]
      form_schema = self.view_func.input_schema["form"]

      if not data_schema.is_empty():
         request_body = self.request.body.decode()
         if not request_body:
            request_body = "{}"
         data = data_schema.validate_via_request(get_json_dict(request_body), context=context)
         data = data.__dict__
      else:
         data = {}

      if not form_schema.is_empty():
         form = form_schema.validate_via_request(dict(self.request.POST), context=context)
         form = form.__dict__
      else:
         form = {}
      query_data = self.view_func.input_schema["query"].model_validate({
         **self.view_kwargs,
         **dict(self.request.GET)
      }, context=context)

      destructured_object_data = {
         **query_data.__dict__,
         **data,
         **form,
      }
      return destructured_object_data

   def set_request_data(self):
      """
      Returns all the data in the self.request.
      """
      if self.view_kwargs:
         self.line_kwargs.update(self.view_kwargs)
      self.query_data.update(dict(self.request.GET))

      if self.request.method != 'GET':
         if self.request.POST:
            self.form.update(dict(self.request.POST))


class ResponseDataParser:

   def __init__(self, status: int, data: Any, schemas: Dict[int, Union[Type[Schema], type]], request: HttpRequest,
                input_data: Dict[str, Any] = None):
      self.status = status
      self.data = data
      self.request = request
      self.input_data = input_data
      if not isinstance(schemas, dict):
         raise create_validation_error("Response", "schemas", "invalid_type")
      self.schemas = schemas

   def create_response_model(self):
      """
      Create a Pydantic model on the basis of response schema.
      """
      schema = self.schemas[self.status]
      # Create a dynamic Pydantic model with the schema
      response_model = create_model(
         RESPONSE_OUTPUT_SCHEMA_NAME,
         **{JSON_OUTPUT_PARSE_NAME: (schema, ...)},
         __base__=Schema
      )
      return response_model

   def parse_response_data(self) -> Dict[str, Any]:
      response_model = self.create_response_model()
      validated_obj = response_model.model_validate(
         {JSON_OUTPUT_PARSE_NAME: self.data},
         context={"request": self.request, "input_data": self.input_data}
      )

      # Deconstruct the object data
      destructured_object_data = validated_obj.model_dump(mode="json", by_alias=True)

      return destructured_object_data.get(JSON_OUTPUT_PARSE_NAME)


def get_response_schema_dict(view_func):
   """
   Get the response schema dict from the view function.
   """
   schema_dict_returned = view_func.__annotations__.get('return', None)
   if not isinstance(schema_dict_returned, dict):
      schema_dict_returned = {200: schema_dict_returned}
   return schema_dict_returned
