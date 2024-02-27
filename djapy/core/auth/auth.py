from django.http import HttpRequest


class BaseAuthMechanism:
    def __init__(self, *args, **kwargs):
        self.message_response = None

    def authenticate(self, request: HttpRequest, *args, **kwargs):
        pass

    def authorize(self, request: HttpRequest, *args, **kwargs):
        pass

    def schema(self):
        return {}

    def required_headers(self):
        pass

    def app_schema(self):
        return {}

    def set_message_response(self, message_response: dict):
        self.message_response = message_response


class SessionAuth(BaseAuthMechanism):
    def __init__(self, *args, **kwargs):
        self.message_response = {"message": "You are not authenticated"}
        super().__init__(*args, **kwargs)

    def authenticate(self, request: HttpRequest, *args, **kwargs):
        return self.message_response

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
