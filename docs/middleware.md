# Middleware

Djapy provides a middleware for error handling. You can use it like this:

```python
MIDDLEWARE = [
    # rest of the middlewares
    'djapy.wrappers.mid.HandleErrorMiddleware'
]
```

## HandleErrorMiddleware

This middleware will handle all the errors and return a JSON response with the error message. The
logs will still be shown as usual, but the user will get a JSON response with the error message.

### Why HandleErrorMiddleware?

Django's default error handling is not good enough for APIs. It returns a HTML response with the
error message, which might cause problems for the client while parsing the response. So, this
middleware will return a JSON response with the error message.

### I don't want to use HandleErrorMiddleware

If you don't want to use this middleware, you can develop your own middleware. You can use the
following code as a reference:

```python
from django.http import JsonResponse
from djapy.utils.prepare_exception import log_exception
from djapy.utils.response_format import create_json

class YourCustomErrorMiddleware:
    """
    Write your own error handling middleware here, according to your needs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        error, display_message = log_exception(request, exception) # use this for getting logs
        error_response = create_json(
            'failed',
            'server_error',
            message=display_message,
            extras={
                'path': request.path,
                'error': error,
            }
        ) # use this for creating a JSON response
        return JsonResponse(error_response, status=500)
```