from django.http import HttpRequest


class BaseAuthMechanism:
    def __init__(self, permissions: list[str] = None, message_response: dict = None, *args, **kwargs):
        self.message_response = message_response or {"message": "Unauthorized"}
        self.permissions = permissions

    def authenticate(self, request: HttpRequest, *args, **kwargs):
        pass

    def authorize(self, request: HttpRequest, *args, **kwargs):
        pass

    def schema(self):
        return {}

    def app_schema(self):
        return {}

    def set_message_response(self, message_response: dict):
        self.message_response = message_response


class SessionAuth(BaseAuthMechanism):

    def authenticate(self, request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return {
                "message": "Unauthorized",
                "alias": "access_denied"
            }

    def authorize(self, request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated or not all([request.user.has_perm(perm) for perm in self.permissions]):
            return {
                "message": "Unauthorized",
                "alias": "permission_denied"
            }

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
