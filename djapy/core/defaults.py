from typing import Literal

SESSION_AUTH = "SESSION"
DEFAULT_METHOD_NOT_ALLOWED_MESSAGE = {"message": "Method not allowed", "alias": "method_not_allowed"}
ALLOW_METHODS_LITERAL = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT"]
DEFAULT_MESSAGE_ERROR = {"message": "Something went wrong", "alias": "server_error"}
