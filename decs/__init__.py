from django.http import JsonResponse

from djapy import JsonNode


def node_to_json_response(func):
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param func: A function that returns a JsonNodify object.
    :return: A JsonResponse.
    """

    def wrapper(*args, **kwargs) -> JsonResponse:
        return func(*args, **kwargs).nodify()

    return wrapper


def model_to_json_node(model_fields: list | str, node_bounded_mode: str = "__strict__") -> callable:
    """
    Use this decorator to return a JsonResponse from a function that returns a JsonNodify object.

    :param model_fields: A function that returns a JsonNodify object.
    :param node_bounded_mode: A function that returns a JsonNodify object.
    :return: A JsonResponse.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            model_object = func(*args, **kwargs)
            return JsonNode(model_object, model_fields, node_bounded_mode=node_bounded_mode)

        return wrapper

    return decorator
