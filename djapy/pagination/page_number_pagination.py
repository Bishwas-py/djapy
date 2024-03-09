from typing import Generic

from django.core.paginator import Paginator, EmptyPage
from django.db.models import QuerySet
from pydantic import model_validator

from djapy.pagination import BasePagination
from djapy.core.typing_utils import G_TYPE
from djapy.schema import Schema

from pydantic import conint

__all__ = ["PageNumberPagination"]


class PageNumberPagination(BasePagination):
    """Pagination based on Page Number."""

    query = [
        ('page_number', conint(ge=1), 1),
        ('page_size', conint(gt=0), 10)
    ]

    class response(Schema, Generic[G_TYPE]):
        items: G_TYPE = []
        has_next: bool = False
        has_previous: bool = False
        num_pages: int = 0
        current_page: int = 0

        @model_validator(mode="before")
        def make_data(cls, queryset, info):
            if not isinstance(queryset, QuerySet):
                raise ValueError("The result should be a QuerySet")

            page_number = info.context['input_data']['page_number']
            page_size = info.context['input_data']['page_size']

            paginator = Paginator(queryset, page_size)

            try:
                page_obj = paginator.page(page_number)
            except EmptyPage:
                return {
                    "items": [],
                    "has_next": False,
                    "has_previous": False,
                    "num_pages": paginator.num_pages,
                    "current_page": page_number
                }

            return {
                "items": page_obj.object_list,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "num_pages": paginator.num_pages,
                "current_page": page_number
            }
