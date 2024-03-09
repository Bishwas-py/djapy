from typing import Generic
from django.db.models import QuerySet
from pydantic import model_validator, conint

from djapy.core.pagination import BasePagination
from djapy.core.typing_utils import G_TYPE
from djapy.schema import Schema

__all__ = ["CursorPagination"]


class CursorPagination(BasePagination):
    """Cursor-based pagination."""

    query = [
        ('cursor', str, '0'),
        ('limit', conint(gt=0), 10)
    ]

    class response(Schema, Generic[G_TYPE]):
        items: G_TYPE
        cursor: str
        limit: int
        has_next: bool

        @model_validator(mode="before")
        def make_data(cls, queryset, info):
            if not isinstance(queryset, QuerySet):
                raise ValueError("The result should be a QuerySet")

            cursor = info.context['input_data']['cursor']
            limit = info.context['input_data']['limit']

            queryset = queryset.order_by('id')  # order by some field in a unique, sequential manner
            # Convert the cursor to integer and get the subset
            cursor = int(cursor)
            queryset_subset = queryset.filter(id__gt=cursor)[:limit]

            has_next = len(queryset.filter(id__gt=cursor)) > limit

            # After processing the queryset, the cursor will be set to the id of the last item
            cursor = str(queryset_subset.last().id) if has_next else None

            return {
                "items": queryset_subset,
                "cursor": cursor,
                "limit": limit,
                "has_next": has_next,
            }
