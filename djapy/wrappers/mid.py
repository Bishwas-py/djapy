from django.http import JsonResponse, HttpResponse
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

    @staticmethod
    def process_exception(request, exception):
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


class UHandleErrorMiddleware:
    """
    Middleware to handle exceptions and return a JsonResponse.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code >= 400 and not isinstance(response, JsonResponse):
            error_response = create_json(
                'failed',
                'u_server_error',
                message="An error occurred while processing your request.",
                extras={
                    'reason': response.reason_phrase,
                    'path': request.path,
                }
            )
            return JsonResponse(error_response, status=response.status_code)
        return response
