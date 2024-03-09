from typing import Generic
from django.db.models import QuerySet
from pydantic import model_validator, conint

from djapy.pagination import BasePagination
from djapy.core.typing_utils import G_TYPE
from djapy.schema import Schema

__all__ = ["CursorPagination"]


class CursorPagination(BasePagination):
    """Cursor-based pagination."""

    query = [
        ('cursor', conint(ge=0), 0),
        ('limit', conint(ge=0), 1)
    ]

    class response(Schema, Generic[G_TYPE]):
        items: G_TYPE
        cursor: int | None
        limit: int
        has_next: bool

        @model_validator(mode="before")
        def make_data(cls, queryset, info):
            if not isinstance(queryset, QuerySet):
                raise ValueError("The result should be a QuerySet")

            cursor = info.context['input_data']['cursor']
            limit = info.context['input_data']['limit']

            queryset = queryset.order_by('id')

            queryset_with_cursor = queryset.filter(id__gt=cursor)

            has_next = queryset_with_cursor.count() > limit

            queryset_subset = list(queryset_with_cursor[:limit])

            cursor = queryset_subset[-1].id if queryset_subset and has_next else None

            return {
                "items": queryset_subset,
                "cursor": cursor,
                "limit": limit,
                "has_next": has_next,
            }
