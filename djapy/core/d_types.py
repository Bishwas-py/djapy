import inspect
from typing import Literal, List, Union, Optional, Type, Dict

from djapy.schema.schema import Schema, Form, QueryMapperSchema

from .auth.auth import BaseAuthMechanism


class dyp:
   methods_literal = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT"]
   methods = List[methods_literal]
   auth = Union[Type[BaseAuthMechanism], BaseAuthMechanism]
   schema = Dict[int, Type[Union[Schema, Form]]]
   inp_schema = Dict[str, Type[Union[Schema, Form, QueryMapperSchema]]]
   resp_params = Optional[inspect.Parameter]
   params = List[inspect.Parameter]