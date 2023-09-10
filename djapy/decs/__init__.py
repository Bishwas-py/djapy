from djapy.decs.wrappers import node_to_json_response, model_to_json_node, method_to_view


def merge_decorators_with_args(decorator_args):
    """
    Merges multiple decorators into one, each with its own arguments.

    :param decorator_args: A list of tuples where each tuple contains (decorator_function, decorator_args).
    :return: A single decorator function that applies all the decorators with their respective arguments.
    """

    def merge_decorator(view_func):
        for decorator, args in decorator_args:
            if args:
                view_func = decorator(*args)(view_func)
            else:
                view_func = decorator(view_func)
        return view_func

    return merge_decorator


def djapy_model_view(model_fields: str | list, is_strictly_bounded: bool):
    decorators_with_args = [
        (method_to_view, []),
        (model_to_json_node, [model_fields, is_strictly_bounded]),
        (node_to_json_response, []),
    ]

    return merge_decorators_with_args(decorators_with_args)
