__all__ = ['as_json', 'as_form', 'uni_schema', 'status_codes', 'is_payload_type']

from http.client import responses
from inspect import Parameter
from typing import Type, TypedDict, Literal

from .schema import Schema
from djapy.core.typing_utils import G_TYPE


class StatusCodes:
   def __init__(self):
      self.success_2xx = {code for code in range(200, 300) if code in responses}
      self.error_4xx = {code for code in range(400, 500) if code in responses}
      self.server_error_5xx = {code for code in range(500, 600) if code in responses}

   @property
   def all(self):
      return {code for code in self.success_2xx | self.error_4xx | self.server_error_5xx}


class ReSchema:
   """
   This class is used to generate response schemas for different status codes.
   """

   def __call__(self, schema: Schema | Type[TypedDict],
                status_set=None):
      """
      :param schema: The schema to be used.
      :param status_set: The status codes to be used. Default is None. If None, all status codes are used `(2xx, 4xx, 5xx)`.
      """
      if status_set is None:
         status_set = {code for code in status_codes.all}
      return {code: schema for code in status_set}

   def success_2xx(self, schema):
      return self.__call__(schema, status_codes.success_2xx)

   def error_4xx(self, schema):
      return self.__call__(schema, status_codes.error_4xx)

   def server_error_5xx(self, schema):
      return self.__call__(schema, status_codes.server_error_5xx)

   def all(self, schema):
      return self.__call__(schema, status_codes.all)


class Payload:
   unquery_type: G_TYPE | None = None

   def __init__(self,
                cvar_c_type: Literal["application/json", "application/x-www-form-urlencoded"] = "application/json"):
      self.cvar_c_type = cvar_c_type

   def __call__(self, type_: G_TYPE) -> G_TYPE:
      """
      Enforces any type to be received as a payload.
      """
      self.unquery_type = type_
      return self


def is_payload_type(param: Parameter) -> Payload | None:
   if param and isinstance(param, Payload):
      return param


as_json = Payload()
as_form = Payload("application/x-www-form-urlencoded")

uni_schema = ReSchema()  # uni_schema is short for unified schema
status_codes = StatusCodes()
