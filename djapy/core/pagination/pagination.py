from functools import wraps

from django.core.paginator import Paginator
from typing import Type, Any, Optional, Union, Tuple, List, Dict, Literal, Generic, TypeVar

from django.db.models import QuerySet
from pydantic import create_model, model_validator, field_validator

from djapy.schema import Schema

T = TypeVar('T')


class OffsetLimitPagination:
    """Pagination based on offset and limit."""

    query = [
        ('offset', int, 10),
        ('limit', int, 0)
    ]

    class response(Schema, Generic[T]):
        result: T
        offset: int
        limit: int

        @model_validator(mode="before")
        def make_data(cls, v, values):
            queryset = v
            if not isinstance(queryset, QuerySet):
                raise ValueError("The result should be a QuerySet")
            offset = values.context['request'].GET.get('offset', 1) or 1
            limit = values.context['request'].GET.get('limit', 10) or 10

            pagination = Paginator(queryset, limit)
            page = pagination.page(offset)
            return {
                "result": page.object_list,
                "offset": page.number,
                "limit": page.paginator.per_page,
            }
