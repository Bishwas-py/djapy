from functools import wraps
from django.http import JsonResponse


def djapy_login_required(
        function: callable = None,
        response_data: dict | None = None
):
    """
    Decorator for views that checks that the user is logged in and returns a JSON response
    if the user is not authenticated.
    """
    if response_data is None:
        response_data = {
            'message': "You're not authorized to perform this action",
            'alias': 'not_authorized',
            'status': 403
        }
    if not isinstance(response_data, dict):
        raise TypeError(
            f'json_response must be a dict, not {type(response_data)}'
        )

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            else:
                return JsonResponse(response_data, status=403)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator
