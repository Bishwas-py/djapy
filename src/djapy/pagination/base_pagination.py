from typing import Generic, ClassVar, Optional, Any
from functools import lru_cache

from djapy.schema import Schema
from djapy.core.typing_utils import G_TYPE


class BasePagination:
   """
   Minimal, unopinionated base class for pagination.
   
   Subclasses define:
   - `query`: List of (name, type, default) for pagination parameters
   - `response`: Schema class for paginated response
   
   The decorator handles:
   - Adding query parameters to view schema
   - Validating parameters
   - Filtering them out before calling view
   - Passing QuerySet result to response validator
   
   Views don't need **kwargs - pagination parameters are auto-consumed!
   """

   query: ClassVar[list] = []

   @classmethod
   @lru_cache(maxsize=32)
   def get_query_params(cls) -> dict:
      """Cached query parameter extraction."""
      return {
         name: (type_name, default)
         for name, type_name, default in cls.query
      }
   
   @classmethod
   @lru_cache(maxsize=32)
   def get_param_names(cls) -> set:
      """Get set of parameter names for filtering."""
      return {name for name, _, _ in cls.query}

   class response(Schema, Generic[G_TYPE]):
      """Base response schema for pagination."""
      pass
