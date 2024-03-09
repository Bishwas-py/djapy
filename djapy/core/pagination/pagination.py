import math

from django.core.paginator import Paginator, EmptyPage
from typing import Generic, TypeVar

from django.db.models import QuerySet
from pydantic import model_validator, conint

from djapy.schema import Schema

T = TypeVar('T')


class BasicPagination:
    """
    Basic pagination with no features implemented. This is the structure of the pagination.
    """
    query = []

    class response(Schema, Generic[T]):
        pass


class OffsetLimitPagination:
    """Pagination based on offset and limit."""

    query = [
        ('offset', conint(ge=0), 0),
        ('limit', conint(gt=0), 10)
    ]

    def __repr__(self):
        return f"OffsetLimitPagination({self.query})"

    class response(Schema, Generic[T]):
        items: T
        offset: int
        limit: int
        has_next: bool
        has_previous: bool
        total_pages: int

        def __repr__(self):
            return f"{T.__name__} with offset {self.offset} and limit {self.limit}"

        @model_validator(mode="before")
        def make_data(cls, queryset, info):
            if not isinstance(queryset, QuerySet):
                raise ValueError("The result should be a QuerySet")

            input_data = info.context['input_data']
            offset = input_data['offset']
            limit = input_data['limit']

            if len(queryset) == 0 or offset > len(queryset):
                return []

            queryset_subset = queryset[offset:offset + limit]

            return {
                "items": queryset_subset,
                "offset": offset,
                "limit": limit,
                "has_next": len(queryset_subset) == limit,
                "has_previous": offset > 0,
                "total_pages": int(math.ceil(len(queryset) / limit)),
            }
