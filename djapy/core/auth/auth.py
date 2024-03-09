from django.http import HttpRequest


class BaseAuthMechanism:
    def __init__(self, permissions: list[str] = None, message_response: dict = None, *args, **kwargs):
        self.message_response = message_response or {"message": "Unauthorized"}
        self.permissions = permissions or []

    def authenticate(self, request: HttpRequest, *args, **kwargs) -> tuple[int, dict] | None:
        pass

    def authorize(self, request: HttpRequest, *args, **kwargs) -> tuple[int, dict] | None:
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
            return 403, {
                "message": "Unauthorized",
                "alias": "access_denied"
            }

    def authorize(self, request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.has_perms(self.permissions):
            return 403, {
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


"""

Something of this syntax. And it could be able to apply pagination details in swagger/OpenAPI too.

@djapify
@djapily_paginated(OffsetLimitPagination)
def related_post(request, search_topic: str) -> {200: list[UserSchema], 401: ErrorMessage}:
    posts = Post.objects.filter(topic__icontains=search_topic)
    return 200, posts

"""
