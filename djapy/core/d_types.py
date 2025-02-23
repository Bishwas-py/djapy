import inspect
from typing import Literal, List, Union, Optional, Type, Dict, TypeAlias, Tuple, Any

from djapy.schema.schema import Schema, Form, QueryMapperSchema

from .auth.auth import BaseAuthMechanism

ResponseDict: TypeAlias = Dict[int, Type[Union[Schema, Form]]]
ResponseTuple: TypeAlias = Union[
    Tuple[int, Any],  # Single tuple response
    Union[Tuple[int, Any], ...]  # Union of tuple responses
]
ResponseType: TypeAlias = Union[ResponseDict, ResponseTuple]


class dyp:
   methods_literal = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT"]
   methods = List[methods_literal]
   auth = Union[Type[BaseAuthMechanism], BaseAuthMechanism]
   schema = Dict[int, Type[Union[Schema, Form]]]
   inp_schema = Dict[str, Type[Union[Schema, Form, QueryMapperSchema]]]
   resp_params = Optional[inspect.Parameter]
   params = List[inspect.Parameter]
