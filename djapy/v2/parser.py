import json
from pydantic import ValidationError, create_model
from django.http import JsonResponse

from djapy.schema import Schema


class RequestDataParser:

    def __init__(self, required_params):
        self.required_params = required_params

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

    def parse_request_data(self, request):
        """
        Parse the request data and validate it with the data model.
        """
        data_model = self.create_data_model()
        data = self.get_request_data(request)

        validated_obj = data_model.parse_obj(data)
        validated_data = validated_obj.dict()

        # Destructure the validated data to the first level
        destructured_data = {k: v.dict() if hasattr(v, "dict") else v for k, v in validated_data.items()}
        return destructured_data

    def get_request_data(self, request):
        """
        Returns all the data in the request.
        """
        param_based_data = {}
        for param in self.required_params:
            data = request.GET.dict()
            if request.POST:
                data.update(request.POST.dict())
            elif request_body := request.body.decode():
                data.update(json.loads(request_body))
            param_based_data[param.name] = data
        return param_based_data


def extract_and_validate_request_params(request, required_params, view_kwargs):
    """
    Extracts and validates request parameters from a Django request object.
    :param request: HttpRequest
        The Django request object to extract parameters from.
    :param required_params: list
    """
    parser = RequestDataParser(required_params)
    return parser.parse_request_data(request)
