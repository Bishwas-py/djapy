from functools import wraps
from django.http import JsonResponse

from djapy.data.mapper import DataWrapper, QueryWrapper
from djapy.data.fields import QueryField


def input_required(payloads: str | list | list[tuple[str, type]], queries: str | list[str] | None = None):
    """
    This decorator is used to validate the input fields of a view function.

    Make sure to add **data** and **query** as parameters to the view function. **data** is a DataWrapper object
    that contains the validated input fields. **query** is a QueryWrapper object that contains the validated query
    fields.

    :param payloads: A list of tuples of the form (str, type) where str is the name of the input field and type is the
    :param queries: A list of strings that are the names of the query fields.
    :return: A JsonResponse if the input fields are invalid, else the view function.
    """
    if not isinstance(payloads, list):
        raise TypeError(f'payloads must be a list, not {type(payloads)}')

    if isinstance(payloads, str):
        payloads = [payloads]

    for index, _input_field in enumerate(payloads):
        if not isinstance(_input_field, tuple):
            payloads[index] = (_input_field, str)

    for _input_field_name, _input_field_type in payloads:
        if not isinstance(_input_field_name, str) or not isinstance(_input_field_type, type):
            raise TypeError('payloads must be a list of (str, type) tuples')

    if isinstance(queries, str):
        queries = [queries]

    if not isinstance(queries, list):
        raise TypeError(f'queries must be a list, not {type(queries)}')

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            data = DataWrapper()
            query = QueryWrapper()
            errors = []

            for query_field_name in queries or []:
                if query_field_name not in request.GET:
                    errors.append({
                        'message': f'Query `{query_field_name}` is required',
                        'alias': 'query_not_found',
                        'status': "failed",
                        'field_name': query_field_name,
                        'field_type': 'query'
                    })
                else:
                    query.add_query(query_field_name, request.GET[query_field_name])

            for field_name, field_type in payloads:
                if field_name not in request.POST:
                    errors.append({
                        'message': f'Payload `{field_name}` is required',
                        'alias': 'key_not_found',
                        'status': "failed",
                        'field_name': field_name,
                        'field_type': 'payload'
                    })
                elif not isinstance(request.POST[field_name], field_type):
                    errors.append({
                        'message': f'{field_name} must be of type {field_type}',
                        'alias': 'invalid_type',
                        'status': "failed",
                        'field_name': field_name,
                        'field_type': 'payload'
                    })
                else:
                    data.add_data(field_name, request.POST[field_name])

            if errors:
                return JsonResponse(errors, status=400, safe=False)

            return view_func(request, data=data, query=query, *args, **kwargs)

        return _wrapped_view

    return decorator


def field_required(func):
    pass
