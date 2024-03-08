from django.core.paginator import Paginator, EmptyPage
from typing import Generic, TypeVar

from django.db.models import QuerySet
from pydantic import model_validator, conint

from djapy.schema import Schema

T = TypeVar('T')


class OffsetLimitPagination:
    """Pagination based on offset and limit."""

    query = [
        ('offset', conint(ge=1), 10),
        ('limit', conint(gt=0), 1)
    ]

    class response(Schema, Generic[T]):
        result: T
        offset: int
        limit: int
        has_next: bool
        has_previous: bool

        @model_validator(mode="before")
        def make_data(cls, queryset, info):
            if not isinstance(queryset, QuerySet):
                raise ValueError("The result should be a QuerySet")

            input_data = info.context['input_data']
            offset = input_data['offset']
            limit = input_data['limit']

            pagination = Paginator(queryset, limit)
            try:
                page = pagination.page(offset)
            except EmptyPage:
                raise ValueError("Input data limit exceeded available data.")

            return {
                "result": page.object_list,
                "offset": page.number,
                "limit": page.paginator.per_page,
                "has_next": page.has_next(),
                "has_previous": page.has_previous()
            }
