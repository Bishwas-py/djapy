import inspect
from functools import wraps
from typing import Callable

from django.http import HttpRequest, JsonResponse
from pydantic import BaseModel


def djapify(output_schema_or_view_func: BaseModel | Callable = None, *args, **kwargs):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            func = view_func(request, *args, **kwargs)
            model_from_func = output_schema_or_view_func.model_validate(func)
            return JsonResponse(model_from_func.model_dump())

        _wrapped_view.parameters = inspect.signature(view_func).parameters
        _wrapped_view.djapy = True
        _wrapped_view.response_schema = output_schema_or_view_func.model_json_schema()

        return _wrapped_view

    return decorator
