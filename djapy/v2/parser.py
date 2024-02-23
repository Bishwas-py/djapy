import json


from djapy.schema import Schema


def extract_and_validate_request_params(request, required_params: list) -> dict:
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
            data_dict = {}
            is_query = getattr(param_type.Config, "is_query", False)
            if is_query:
                data_dict.update(**request.GET.dict())
            if request.POST:
                data_dict.update(request.POST.dict())
            elif request.body:
                data_dict.update(json.loads(request.body))
            parsed_data[param.name] = param_type(**data_dict)

    return parsed_data
