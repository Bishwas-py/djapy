import json
from pydantic import ValidationError, create_model
from django.http import JsonResponse

from djapy.schema import Schema


class RequestDataParser:

    def __init__(self, request, required_params, view_kwargs):
        self.required_params = required_params
        self.view_kwargs = view_kwargs
        self.request = request

    def create_data_model(self):
        """
        Create a Pydantic model on the basis of required parameters.
        """
        data_model = create_model(
            'input',
            **{param.name: (param.annotation, ...) for param in self.required_params},
            __base__=Schema
        )
        return data_model

    def parse_request_data(self):
        """
        Parse the request data and validate it with the data model.
        """
        data_model = self.create_data_model()
        data = self.get_request_data()
        print(data)
        validated_obj = data_model.parse_obj(data)
        validated_data = validated_obj.dict()

        # Destructure the validated data to the first level
        destructured_data = {k: v for k, v in validated_data.items()}
        return destructured_data

    def get_request_data(self):
        """
        Returns all the data in the self.request.
        """
        param_based_data = {}
        data = self.request.GET.dict()
        if self.view_kwargs:
            data.update(self.view_kwargs)
        if self.request.POST:
            data.update(self.request.POST.dict())
        elif request_body := self.request.body.decode():
            data.update(json.loads(request_body))
        for param in self.required_params:
            if isinstance(param.annotation, Schema):
                param_based_data[param.name] = data
            else:
                param_based_data[param.name] = data.get(param.name, None)
        return param_based_data


def extract_and_validate_request_params(request, required_params, view_kwargs):
    """
    Extracts and validates request parameters from a Django request object.
    :param request: HttpRequest
        The Django request object to extract parameters from.
    :param required_params: list
    :params view_kwargs: dict
    """
    parser = RequestDataParser(request, required_params, view_kwargs)
    return parser.parse_request_data()
