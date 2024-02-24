import json

from djapy.schema import Schema
from djapy.v2.response import create_validation_error


def extract_and_validate_request_params(request, required_params: list, view_kwargs: dict) -> dict:
    """
    Extracts and validates request parameters from a Django request object.
    :param request: HttpRequest
        The Django request object to extract parameters from.
    :param required_params: list
    """
    parsed_data = {}
    for param in required_params:
        param_type = param.annotation
        if issubclass(param_type, Schema):
            is_query = getattr(param_type.Config, "is_query", False) if hasattr(param_type, "Config") else True
            data_dict = {}
            if is_query:
                data_dict.update(**request.GET.dict())
            if request.POST:
                data_dict.update(request.POST.dict())
            elif request.body:
                data_dict.update(json.loads(request.body))
            parsed_data[param.name] = param_type(**data_dict)
        else:
            parsable_value = view_kwargs.get(param.name) or request.GET.get(param.name)
            if parsable_value:
                try:
                    parsed_data[param.name] = param_type(parsable_value)
                except ValueError:
                    raise create_validation_error("input", param_type.__name__, f"{param_type.__name__}_parsing")
            else:
                raise create_validation_error("input", param_type.__name__, "missing")

    return parsed_data
