import json
from inspect import Parameter

from pydantic import create_model, EmailStr

from djapy.schema import Schema
from djapy.v2.response import create_validation_error


class CreateUserSchema(Schema):
    username: str
    email: EmailStr

    class Config:
        is_query = False


class Reason(Schema):
    reason_code: str
    reason_id: int


def extract_and_validate_request_params(request, required_params: list[Parameter], view_kwargs: dict) -> dict:
    """
    Extracts and validates request parameters from a Django request object.
    :param request: HttpRequest
        The Django request object to extract parameters from.
    :param required_params: list
    """
    parsed_data = {}
    print(required_params)
    # create parable modal from required_params
    request_schema_dict = {param.name: (param.annotation, ...) for param in required_params}
    parsable_model = create_model(
        'input',
        **request_schema_dict,
        __base__=Schema
    )
    print(parsable_model.schema())
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
