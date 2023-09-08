def create_response(status: str, alias: str, message: str, data: str = None, extras: dict = None):
    response = {}

    if status:
        response['status'] = status

    if alias:
        response['alias'] = alias

    if message:
        response['message'] = message

    if data:
        response['data']: data

    if extras:
        response = {**response, **extras}

    return response
