import json
from inspect import Parameter
from typing import Dict, Any, Union, Type

from pydantic import ValidationError, create_model, BaseModel, Json
from django.http import JsonResponse, HttpRequest

from djapy.schema import Schema
from .type_check import schema_type
from .response import create_validation_error
from .labels import REQUEST_INPUT_SCHEMA_NAME, RESPONSE_OUTPUT_SCHEMA_NAME, JSON_OUTPUT_PARSE_NAME, JSON_BODY_PARSE_NAME


class RequestDataParser:
    def __init__(self, request: HttpRequest, view_func, view_kwargs):
        self.required_params = view_func.required_params
        self.query_schema = view_func.query_schema
        self.data_schema = view_func.data_schema
        self.view_kwargs = view_kwargs
        self.request = request
        self.query_data = {}
        self.line_kwargs = {}
        self.data = {}

    def parse_request_data(self):
        """
        Parse the request data and validate it with the data model.
        """
        self.set_request_data()
        if len(self.required_params) == 1 and (schema := schema_type(self.required_params[0])):
            validated_obj = schema.validate(self.data)
            destructured_object_data = {
                self.required_params[0].name: validated_obj
            }
        else:
            query_data = self.query_schema.model_validate({
                **self.query_data,
                **self.line_kwargs
            })
            data = self.data_schema.model_validate(self.data)
            destructured_object_data = {
                **query_data.dict(),
                **data.dict()
            }
        return destructured_object_data

    def set_request_data(self):
        """
        Returns all the data in the self.request.
        """
        if self.view_kwargs:
            self.line_kwargs.update(self.view_kwargs)
        self.query_data.update(self.request.GET.dict())

        if self.request.method != 'GET':
            if self.request.POST:
                self.data.update(self.request.POST.dict())
            elif request_body := self.request.body.decode():
                json_modal_schema = create_model(
                    REQUEST_INPUT_SCHEMA_NAME,
                    **{JSON_BODY_PARSE_NAME: (Json, ...)},
                    __base__=BaseModel
                )
                validated_obj = json_modal_schema.model_validate({
                    JSON_BODY_PARSE_NAME: request_body
                })
                self.data.update(validated_obj.dict().get(JSON_BODY_PARSE_NAME))


class ResponseDataParser:

    def __init__(self, status: int, data: Any, schemas: Dict[int, Union[Type[Schema], type]]):
        self.status = status
        self.data = data
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
        validated_obj = response_model.model_validate({JSON_OUTPUT_PARSE_NAME: self.data})

        # Deconstruct the object data
        destructured_object_data = validated_obj.dict()

        return destructured_object_data.get(JSON_OUTPUT_PARSE_NAME)
