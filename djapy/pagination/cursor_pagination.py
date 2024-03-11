from typing import Generic, Literal
from django.db.models import QuerySet
from pydantic import model_validator, conint

from djapy.pagination.base_pagination import BasePagination
from djapy.core.typing_utils import G_TYPE
from djapy.schema import Schema

__all__ = ["CursorPagination"]


class CursorPagination(BasePagination):
    """Cursor-based pagination."""

    query = [
        ('cursor', conint(ge=0) | Literal['null'] | None, None),
        ('limit', conint(ge=1), 1),
        ('ordering', Literal['asc', 'desc'], 'asc'),  # the ordering can be 'asc', 'desc', or None
    ]

    class response(Schema, Generic[G_TYPE]):
        items: G_TYPE
        cursor: int | None
        limit: int
        ordering: Literal['asc', 'desc']
        has_next: bool

        @model_validator(mode="before")
        def make_data(cls, queryset, info):
            if not isinstance(queryset, QuerySet):
                raise ValueError("The result should be a QuerySet")

            cursor = info.context['input_data']['cursor']
            limit = info.context['input_data']['limit']
            ordering = info.context['input_data']['ordering']
            if cursor == 'null':
                cursor = None

            is_cursor_empty = cursor is None
            # apply ordering to the queryset
            if ordering == 'desc':
                queryset = queryset.order_by('-id')  # descending order
            else:  # default to ascending order
                queryset = queryset.order_by('id')  # ascending order

            if not queryset.exists():
                return {
                    "items": [],
                    "cursor": None,
                    "limit": limit,
                    "has_next": False,
                    "ordering": ordering
                }

            if is_cursor_empty:
                cursor = queryset.first().id

            # apply cursor to the queryset
            query_search = {}  # for ascending order
            if is_cursor_empty and ordering == 'desc':
                query_search = {'id__lte': cursor}
            elif is_cursor_empty and ordering == 'asc':
                query_search = {'id__gte': cursor}
            elif ordering == 'desc':
                query_search = {'id__lt': cursor}
            else:
                query_search = {'id__gt': cursor}

            queryset_with_cursor = queryset.filter(**query_search)
            has_next = queryset_with_cursor.count() > limit

            # get subset
            queryset_subset = list(queryset_with_cursor[:limit])

            # set new cursor
            if queryset_subset:
                new_cursor = queryset_subset[-1].id
                cursor = new_cursor if has_next else None
            else:
                cursor = None

            return {
                "items": queryset_subset,
                "cursor": cursor,
                "limit": limit,
                "has_next": has_next,
                "ordering": ordering
            }
