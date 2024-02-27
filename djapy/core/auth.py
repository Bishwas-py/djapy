from django.http import HttpRequest


class BaseAuthMechanism:
    def __init__(self, *args, **kwargs):
        pass

    def authenticate(self, request: HttpRequest, *args, **kwargs):
        pass

    def schema(self):
        pass

    def required_headers(self):
        pass

    def app_schema(self):
        pass


class SessionAuth(BaseAuthMechanism):
    def authenticate(self, request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return {"message": "You are not authenticated"}

    def required_headers(self):
        return [
            "Cookie"
        ]

    def schema(self):
        return {
            "SessionAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "sessionid"
            },
            "CSRFTokenAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "csrftoken"
            }
        }

    def app_schema(self):
        return {
            "SessionAuth": [],
            "CSRFTokenAuth": []
        }
