from typing import Literal, List, Union, Optional, Type

from .auth.auth import BaseAuthMechanism


class Dyp:
   METHODS_LITERAL = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT"]
   METHODS = Union[METHODS_LITERAL, List[METHODS_LITERAL]]
   AUTH = Optional[Union[Type[BaseAuthMechanism], BaseAuthMechanism]]
