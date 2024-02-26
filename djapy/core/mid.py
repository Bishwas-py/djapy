import logging

from django.http import JsonResponse

__all__ = ['UHandleErrorMiddleware']


class UHandleErrorMiddleware:
    """
    Middleware to handle exceptions and return a JsonResponse.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user_agent = request.headers.get('User-Agent')
        is_browser = 'Mozilla/' in user_agent

        if response.status_code >= 400 and not isinstance(response, JsonResponse) and not is_browser:
            error_response = {
                "message": "An error occurred while processing your request.",
                "reason": response.reason_phrase,
                "alias": "server_error"
            }
            return JsonResponse(error_response, status=response.status_code)
        return response
