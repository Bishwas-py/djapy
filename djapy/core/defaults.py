from typing import Literal, List

SESSION_AUTH = "SESSION"
DEFAULT_METHOD_NOT_ALLOWED_MESSAGE = {"message": "Method not allowed", "alias": "method_not_allowed"}
ALLOW_METHODS_LITERAL = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT"]
DEFAULT_MESSAGE_ERROR = {"message": "Something went wrong", "alias": "server_error"}
DEFAULT_AUTH_ERROR = {"message": "Unauthorized"}
ALLOWED_METHODS = ALLOW_METHODS_LITERAL | List[ALLOW_METHODS_LITERAL]