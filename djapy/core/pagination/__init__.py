from typing import Generic

from djapy.core.pagination.offset_pagination import OffsetLimitPagination
from djapy.core.pagination.page_number_pagination import PageNumberPagination
from djapy.schema import Schema
from djapy.core.typing_utils import G_TYPE

__all__ = ["OffsetLimitPagination", "PageNumberPagination", "BasicPagination"]


class BasicPagination:
    """
    Basic pagination with no features implemented. This is the structure of the pagination.
    """

    query = []

    class response(Schema, Generic[G_TYPE]):
        pass
