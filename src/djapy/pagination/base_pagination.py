from typing import Generic

from djapy.schema import Schema
from djapy.core.typing_utils import G_TYPE


class BasePagination:
   """
   Basic pagination with no features implemented. This is the structure of the pagination.
   """

   query = []

   class response(Schema, Generic[G_TYPE]):
      pass
