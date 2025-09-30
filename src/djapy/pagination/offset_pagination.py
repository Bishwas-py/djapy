import math
from typing import Generic
from functools import lru_cache

from django.db.models import QuerySet
from pydantic import model_validator, conint, computed_field

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
      total: int  # Add total count
      has_next: bool
      has_previous: bool
      total_pages: int

      def __repr__(self):
         return f"{G_TYPE.__name__} with offset {self.offset} and limit {self.limit}"

      @computed_field
      @property
      def current_page(self) -> int:
         """Calculate current page number (1-indexed)."""
         if self.limit == 0:
            return 1
         return (self.offset // self.limit) + 1

      @computed_field
      @property
      def items_count(self) -> int:
         """Count of items in current page."""
         return len(self.items) if isinstance(self.items, list) else 0

      @computed_field
      @property
      def start_index(self) -> int:
         """1-indexed start position."""
         return self.offset + 1 if self.total > 0 else 0

      @computed_field
      @property
      def end_index(self) -> int:
         """1-indexed end position."""
         return min(self.offset + self.items_count, self.total)

      @model_validator(mode="before")
      def make_data(cls, queryset, info):
         if not isinstance(queryset, QuerySet):
            raise ValueError("The result should be a QuerySet")

         input_data = info.context['input_data']
         offset = input_data['offset']
         limit = input_data['limit']
         
         # Optimized: single count query with caching hint
         count = queryset.count()

         if count == 0 or offset > count:
            return {
               "items": [],
               "offset": offset,
               "limit": limit,
               "total": count,
               "has_next": False,
               "has_previous": False,
               "total_pages": 0,
            }

         # Get subset - use list() to avoid multiple queries
         queryset_subset = list(queryset[offset:offset + limit])
         items_count = len(queryset_subset)

         return {
            "items": queryset_subset,
            "offset": offset,
            "limit": limit,
            "total": count,
            "has_next": offset + items_count < count,
            "has_previous": offset > 0,
            "total_pages": math.ceil(count / limit) if limit > 0 else 0,
         }
