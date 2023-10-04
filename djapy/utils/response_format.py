from typing import Dict

from django.http import JsonResponse


def create_json(
        status: str,
        alias: str,
        message: str,
        data: dict = None,
        extras: dict = None,
        field_name: str = None,
        field_type: str = None,
        field_value=''
) -> JsonResponse | dict[str, str | dict]:
    """
    A utility function to create a response dictionary.

    :param status: A string value to indicate the status of the response; usually 'success', 'error', 'created', etc.
    :param alias: A string value to indicate the alias of the response; 'todo_fetched', 'employee_created', etc.
    :param message: A string value to indicate the message of the response; 'Employee created successfully.', etc.
    :param data: A dictionary value to indicate the data of the response; {'id': 1, 'name': 'John Doe'}, etc.
    :param extras: A dictionary value to indicate the extra fields of the response; {'path': '/api/v1/employee'}, etc.
    :param field_name: A string value to indicate the name of the field; 'name', 'email', 'password', 'number', etc.
    :param field_type: A string value to indicate the type of the field; 'string', 'integer', etc.
    :param field_value: A string value to indicate the value of the field; 'John Doe', '
    """
    response = {}

    if status:
        response['status'] = status

    if alias:
        response['alias'] = alias

    if message:
        response['message'] = message

    if data:
        response['data'] = data

    if extras:
        response = {**response, **extras}

    if field_name:
        response['field_name'] = str(field_name)

    if field_type:
        response['field_type'] = str(field_type)

    if field_value:
        response['field_value'] = str(field_value)

    return response


def create_response(
        status: str,
        alias: str,
        message: str,
        data: dict = None,
        extras: dict = None,
        field_name: str = None,
        field_type: str = None,
        field_value='',
        auto_status: bool = True,
):
    json_response = JsonResponse(
        create_json(
            status=status,
            alias=alias,
            message=message,
            data=data,
            extras=extras,
            field_name=field_name,
            field_type=field_type,
            field_value=field_value,
        )
        , safe=False, status=200)

    if auto_status and status != 'success':
        if 'server_error' in status:
            json_response.status_code = 500
        elif 'error' in status or 'failed' in status:
            json_response.status_code = 400
        elif 'created' in status:
            json_response.status_code = 201
        elif 'updated' in status or 'success' in status or 'deleted' in status:
            json_response.status_code = 200
        elif 'no_content' in status:
            json_response.status_code = 204
        elif 'not_found' in status:
            json_response.status_code = 404
        elif 'unauthorized' in status or 'forbidden' in status or 'not_allowed' in status:
            json_response.status_code = 401

    return json_response
