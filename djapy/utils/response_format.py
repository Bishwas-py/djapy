def create_response(
        status: str,
        alias: str,
        message: str,
        data: dict = None,
        extras: dict = None,
        field_name: str = None,
        field_type: str = None,
        field_value=''
) -> dict:
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
