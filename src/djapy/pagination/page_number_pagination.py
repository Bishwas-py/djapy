from typing import Generic

from django.core.paginator import Paginator, EmptyPage
from django.db.models import QuerySet
from pydantic import model_validator, conint, computed_field, Field

from djapy.pagination import BasePagination
from djapy.core.typing_utils import G_TYPE
from djapy.schema import Schema

__all__ = ["PageNumberPagination"]


class PageNumberPagination(BasePagination):
   """Pagination based on Page Number."""

   query = [
      ('page_number', conint(ge=1), 1),
      ('page_size', conint(gt=0), 10)
   ]

   class response(Schema, Generic[G_TYPE]):
      items: G_TYPE = Field(default_factory=list)
      current_page: int = Field(ge=1, description="Current page number")
      page_size: int = Field(gt=0, description="Items per page")
      total: int = Field(ge=0, description="Total items count")
      num_pages: int = Field(ge=0, description="Total pages")
      has_next: bool = Field(default=False, description="Has next page")
      has_previous: bool = Field(default=False, description="Has previous page")

      @computed_field
      @property
      def items_count(self) -> int:
         """Count of items in current page."""
         return len(self.items) if isinstance(self.items, list) else 0

      @computed_field
      @property
      def start_index(self) -> int:
         """1-indexed start position."""
         if self.total == 0:
            return 0
         return ((self.current_page - 1) * self.page_size) + 1

      @computed_field
      @property
      def end_index(self) -> int:
         """1-indexed end position."""
         return min(self.start_index + self.items_count - 1, self.total)

      @computed_field
      @property
      def is_first_page(self) -> bool:
         """Check if this is the first page."""
         return self.current_page == 1

      @computed_field
      @property
      def is_last_page(self) -> bool:
         """Check if this is the last page."""
         return self.current_page == self.num_pages or self.num_pages == 0

      @model_validator(mode="before")
      def make_data(cls, queryset, info):
         """Optimized page number pagination."""
         if not isinstance(queryset, QuerySet):
            raise ValueError("The result should be a QuerySet")

         page_number = info.context['input_data']['page_number']
         page_size = info.context['input_data']['page_size']

         # Use Django's efficient Paginator
         paginator = Paginator(queryset, page_size)
         total = paginator.count  # Cached count

         try:
            page_obj = paginator.page(page_number)
            items = list(page_obj.object_list)  # Evaluate queryset once
         except EmptyPage:
            return {
               "items": [],
               "current_page": page_number,
               "page_size": page_size,
               "total": total,
               "num_pages": paginator.num_pages,
               "has_next": False,
               "has_previous": False,
            }

         return {
            "items": items,
            "current_page": page_number,
            "page_size": page_size,
            "total": total,
            "num_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
         }
