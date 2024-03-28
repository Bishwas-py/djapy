from typing import Dict, Any, Union, Type

from pydantic import create_model, BaseModel, Json
from django.http import HttpRequest

from djapy.schema import Schema
from .response import create_validation_error
from .labels import REQUEST_INPUT_SCHEMA_NAME, RESPONSE_OUTPUT_SCHEMA_NAME, JSON_OUTPUT_PARSE_NAME, JSON_BODY_PARSE_NAME

__all__ = ['RequestDataParser', 'ResponseDataParser', 'get_response_schema_dict']


class RequestDataParser:
    def __init__(self, request: HttpRequest, view_func, view_kwargs):
        self.view_func = view_func
        self.query_schema = view_func.query_schema
        self.data_schema = view_func.data_schema
        self.single_data_schema = view_func.single_data_schema
        self.single_data_key = view_func.single_data_key
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
        context = {"request": self.request}
        if self.single_data_schema:
            validated_obj = self.single_data_schema.model_validate(self.data, context=context)
            destructured_data_dict = {self.single_data_key: validated_obj}
        else:
            data = self.data_schema.model_validate(self.data, context=context)
            destructured_data_dict = data.__dict__

        query_data = self.query_schema.model_validate({
            **self.query_data,
            **self.line_kwargs
        }, context=context)
        destructured_object_data = {
            **query_data.__dict__,
            **destructured_data_dict
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
