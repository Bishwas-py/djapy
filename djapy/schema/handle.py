__all__ = ['payload', 'uni_schema', 'status_codes']

from http.client import responses
from typing import Type, TypedDict

from .schema import Schema
from djapy.core.typing_utils import G_TYPE


class StatusCodes:
    def __init__(self):
        self.success_2xx = {code for code in range(200, 300) if code in responses}
        self.error_4xx = {code for code in range(400, 500) if code in responses}
        self.server_error_5xx = {code for code in range(500, 600) if code in responses}

    @property
    def all(self):
        return {code for code in self.success_2xx | self.error_4xx | self.server_error_5xx}


class ReSchema:
    """
    This class is used to generate response schemas for different status codes.
    """

    def __call__(self, schema: Schema | Type[TypedDict],
                 status_set=None):
        """
        :param schema: The schema to be used.
        :param status_set: The status codes to be used. Default is None. If None, all status codes are used `(2xx, 4xx, 5xx)`.
        """
        if status_set is None:
            status_set = {code for code in status_codes.all}
        return {code: schema for code in status_set}

    def success_2xx(self, schema):
        return self.__call__(schema, status_codes.success_2xx)

    def error_4xx(self, schema):
        return self.__call__(schema, status_codes.error_4xx)

    def server_error_5xx(self, schema):
        return self.__call__(schema, status_codes.server_error_5xx)

    def all(self, schema):
        return self.__call__(schema, status_codes.all)


class Payload:
    unquery_type: G_TYPE | None = None

    def __call__(self, type_: G_TYPE) -> G_TYPE:
        """
        Enforces any type to be received as a payload.
        """
        self.unquery_type = type_
        return self


payload = Payload()
uni_schema = ReSchema()  # uni_schema is short for unified schema
status_codes = StatusCodes()
