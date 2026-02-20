from typing import Generic, Literal, Optional
from django.db.models import QuerySet
from pydantic import model_validator, conint, computed_field, Field

from djapy.pagination.base_pagination import BasePagination
from djapy.core.typing_utils import G_TYPE
from djapy.schema import Schema

__all__ = ["CursorPagination"]


class CursorPagination(BasePagination):
   """
   Cursor-based pagination using a field as the cursor position.
   
   By default uses 'id' field. Override `cursor_field` to use a different field:
   
   Example:
       class TimestampCursorPagination(CursorPagination):
           cursor_field = 'created_at'
   """

   cursor_field: str = 'id'  # Field to use for cursor position
   
   query = [
      ('cursor', conint(ge=0) | Literal['null'] | None, None),
      ('limit', conint(ge=1), 1),
      ('ordering', Literal['asc', 'desc'], 'asc'),
   ]

   class response(Schema, Generic[G_TYPE]):
      items: G_TYPE
      cursor: Optional[int] = Field(None, description="Next cursor position")
      limit: int = Field(gt=0, description="Items per page")
      ordering: Literal['asc', 'desc'] = Field(description="Sort order")
      has_next: bool = Field(description="More items available")

      @computed_field
      @property
      def items_count(self) -> int:
         """Count of items in current page."""
         return len(self.items) if isinstance(self.items, list) else 0

      @computed_field
      @property
      def is_first_page(self) -> bool:
         """Check if this is the first page."""
         return self.cursor is None or not self.has_next

      @computed_field
      @property
      def is_last_page(self) -> bool:
         """Check if this is the last page."""
         return not self.has_next

      @model_validator(mode="before")
      def make_data(cls, queryset, info):
         """Optimized cursor pagination with better performance."""
         if not isinstance(queryset, QuerySet):
            raise ValueError("The result should be a QuerySet")

         cursor = info.context['input_data']['cursor']
         limit = info.context['input_data']['limit']
         ordering = info.context['input_data']['ordering']
         
         # Normalize cursor
         if cursor == 'null':
            cursor = None

         is_cursor_empty = cursor is None
         
         # Get cursor field - can be customized by subclassing
         # Access from the pagination class that was passed to @paginate()
         pagination_class = info.context.get('pagination_class', CursorPagination)
         order_field = getattr(pagination_class, 'cursor_field', 'id')
         
         # Apply ordering
         if ordering == 'desc':
            queryset = queryset.order_by(f'-{order_field}')
         else:
            queryset = queryset.order_by(order_field)

         # Early return for empty queryset
         if not queryset.exists():
            return {
               "items": [],
               "cursor": None,
               "limit": limit,
               "has_next": False,
               "ordering": ordering
            }

         # Set initial cursor if not provided
         if is_cursor_empty:
            first_obj = queryset.first()
            cursor = getattr(first_obj, order_field)

         # Build cursor filter (optimized)
         if is_cursor_empty and ordering == 'desc':
            query_search = {f'{order_field}__lte': cursor}
         elif is_cursor_empty and ordering == 'asc':
            query_search = {f'{order_field}__gte': cursor}
         elif ordering == 'desc':
            query_search = {f'{order_field}__lt': cursor}
         else:
            query_search = {f'{order_field}__gt': cursor}

         queryset_with_cursor = queryset.filter(**query_search)
         
         # Fetch limit + 1 to check for next page (single query)
         queryset_subset = list(queryset_with_cursor[:limit + 1])
         has_next = len(queryset_subset) > limit
         
         # Trim to actual limit
         if has_next:
            queryset_subset = queryset_subset[:limit]

         # Set new cursor
         if queryset_subset and has_next:
            new_cursor = getattr(queryset_subset[-1], order_field)
            cursor = new_cursor
         else:
            cursor = None

         return {
            "items": queryset_subset,
            "cursor": cursor,
            "limit": limit,
            "has_next": has_next,
            "ordering": ordering
         }
