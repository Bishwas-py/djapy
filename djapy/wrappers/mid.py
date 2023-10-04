from django.http import JsonResponse
from djapy.utils.prepare_exception import log_exception
from djapy.utils.response_format import create_json


class HandleErrorMiddleware:
    """
    Middleware to handle exceptions and return a JsonResponse.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        error, display_message = log_exception(request, exception)
        error_response = create_json(
            'failed',
            'server_error',
            message=display_message,
            extras={
                'path': request.path,
                'error': error,
            }
        )
        return JsonResponse(error_response, status=500)
