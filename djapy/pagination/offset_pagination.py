import math

from typing import Generic
from django.db.models import QuerySet
from pydantic import model_validator, conint

from djapy.pagination import BasePagination
from djapy.core.typing_utils import G_TYPE
from djapy.schema import Schema

__all__ = ["OffsetLimitPagination"]


class OffsetLimitPagination(BasePagination):
   """Pagination based on offset and limit."""

   query = [
      ('offset', conint(ge=0), 0),
      ('limit', conint(gt=0), 10)
   ]

   def __repr__(self):
      return f"OffsetLimitPagination({self.query})"

   class response(Schema, Generic[G_TYPE]):
      items: G_TYPE
      offset: int
      limit: int
      has_next: bool
      has_previous: bool
      total_pages: int

      def __repr__(self):
         return f"{G_TYPE.__name__} with offset {self.offset} and limit {self.limit}"

      @model_validator(mode="before")
      def make_data(cls, queryset, info):
         if not isinstance(queryset, QuerySet):
            raise ValueError("The result should be a QuerySet")

         input_data = info.context['input_data']
         offset = input_data['offset']
         limit = input_data['limit']

         if queryset.count() == 0 or offset > queryset.count():
            return {
               "items": [],
               "offset": offset,
               "limit": limit,
               "has_next": False,
               "has_previous": False,
               "total_pages": 0,
            }

         queryset_subset = queryset[offset:offset + limit]

         return {
            "items": queryset_subset,
            "offset": offset,
            "limit": limit,
            "has_next": queryset_subset.count() == limit,
            "has_previous": offset > 0,
            "total_pages": math.ceil(queryset.count() / limit),
         }
