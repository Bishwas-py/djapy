import copy
import inspect
import json
from functools import wraps

from django.http import HttpRequest, JsonResponse, QueryDict
from django.http.multipartparser import MultiPartParser

from djapy.data.fields import get_field_object, get_request_value, get_request_data
from djapy.data.mapper import DataWrapper, QueryWrapper
from djapy.utils.response_format import create_response


def input_required(payloads: str | list | list[tuple[str, type]], queries: str | list[str] | None = None):
    """
    This decorator is used to validate the input fields of a view function, and attach the validated input fields to
    the view function.

    Make sure to add **data** and **query** as parameters to the view function. **data** is a DataWrapper object
    that contains the validated input fields. **query** is a QueryWrapper object that contains the validated query
    fields.

    :param payloads: A list of tuples of the form (str, type) where str is the name of the input field and type is the
    :param queries: A list of strings that are the names of the query fields.
    :return: A JsonResponse if the input fields are invalid, else the view function.
    """

    if queries is None:
        queries = []

    if isinstance(payloads, str):
        payloads = [payloads]

    if not isinstance(payloads, list):
        raise TypeError(f'Payloads must be a list, not {type(payloads)}')

    for index, _input_field in enumerate(payloads):
        if not isinstance(_input_field, tuple):
            payloads[index] = (_input_field, str)

    for _input_field_name, _input_field_type in payloads:
        if not isinstance(_input_field_name, str) or not isinstance(_input_field_type, type):
            raise TypeError('Payloads must be a list of (str, type) tuples')

    if isinstance(queries, str):
        queries = [queries]

    if not isinstance(queries, list):
        raise TypeError(f'Queries must be a list, not {type(queries)}')

    def decorator(view_func):

        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            request_data = get_request_data(request)

            data = DataWrapper()
            query = QueryWrapper()
            errors = []

            for query_field_name in queries:
                if query_field_name not in request.GET:
                    errors.append(create_response(
                        'failed', 'query_not_found', f'Query `{query_field_name}` is required',
                        extras={'field_name': query_field_name, 'field_type': 'query'}
                    ))
                else:
                    query.add_query(query_field_name, request.GET[query_field_name])

            for field_name, field_type in payloads:
                if field_name not in request_data:
                    errors.append(create_response(
                        'failed', 'payload_not_found', f'Payload `{field_name}` is required',
                        extras={'field_name': field_name, 'field_type': 'payload'}
                    ))
                elif not isinstance(request_data[field_name], field_type):
                    errors.append(create_response(
                        "failed", "invalid_type", f"{field_name} must be of type {field_type}",
                        extras={'field_name': field_name, 'field_type': 'payload'}
                    ))
                else:
                    data.add_data(field_name, request_data[field_name])

            if errors:
                return JsonResponse(errors, status=400, safe=False)

            params = list(inspect.signature(view_func).parameters.keys())

            if 'data' in params:
                kwargs['data'] = data
            if 'query' in params:
                kwargs['query'] = query
            if '_data' in params:
                kwargs['_data'] = request_data

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def field_required(func):
    """
    This decorator is used to validate the input fields of a view function, and attach the validated input fields to
    the view function according to provided annotations.
    """
    query_class = func.__annotations__.get("query")
    data_class = func.__annotations__.get("data")
    query_object, query_items = get_field_object(query_class)
    data_object, data_items = get_field_object(data_class)

    if query_items is None:
        query_items = []
    if data_items is None:
        data_items = []

    def wrapper(request: HttpRequest, *args, **kwargs):
        request_data = get_request_data(request)
        new_query_object = copy.deepcopy(query_object)
        new_data_object = copy.deepcopy(data_object)

        errors = []

        for query_name, query_type in query_items:
            query_value = get_request_value(request.GET, query_name, query_type)
            if query_value is None:
                errors.append(create_response(
                    'failed', 'query_not_found', f'Query `{query_name}` is required',
                    extras={'field_name': query_name, 'field_type': 'query'}
                ))
            else:
                setattr(new_query_object, query_name, query_value)

        for data_name, data_type in data_items:
            data_value = get_request_value(request_data, data_name, data_type)
            if data_value is None:
                errors.append(create_response(
                    'failed', 'data_not_found', f'Data `{data_name}` is required',
                    extras={'field_name': data_name, 'field_type': 'data'}
                ))
            else:
                setattr(new_data_object, data_name, data_value)

        if query_class is not None:
            kwargs['query'] = new_query_object

        if data_class is not None:
            kwargs['data'] = new_data_object

        if '_data' in func.__annotations__:
            kwargs['_data'] = request_data

        if errors:
            return JsonResponse(errors, status=400, safe=False)
        return func(request, *args, **kwargs)

    return wrapper
