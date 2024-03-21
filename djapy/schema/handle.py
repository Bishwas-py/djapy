__all__ = ['payload', 'uni_schema', 'StatusCodes']

from http.client import responses
from typing import Type, TypedDict, Literal

from .schema import Schema
from djapy.core.typing_utils import G_TYPE


class StatusCodes:
    success_2xx = {code for code in range(200, 300) if code in responses}
    error_4xx = {code for code in range(400, 500) if code in responses}
    server_error_5xx = {code for code in range(500, 600) if code in responses}


class ReSchema:
    def __call__(self, schema: Schema | Type[TypedDict] | Literal[*StatusCodes.__annotations__],
                 status_set=None):
        if status_set is None:
            status_set = StatusCodes.success_2xx
        return {code: schema for code in status_set}

    def success_2xx(self, schema):
        return self.__call__(schema, StatusCodes.success_2xx)

    def error_4xx(self, schema):
        return self.__call__(schema, StatusCodes.error_4xx)

    def server_error_5xx(self, schema):
        return self.__call__(schema, StatusCodes.server_error_5xx)


class Payload:
    unquery_type: G_TYPE | None = None

    def __call__(self, type_: G_TYPE) -> G_TYPE:
        """
        Enforces any type to be received as a payload.
        """
        self.unquery_type = type_
        return self


payload = Payload()
uni_schema = ReSchema()
