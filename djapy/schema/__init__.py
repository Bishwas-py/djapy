from typing import Generic

from pydantic import BaseModel

__all__ = ['Schema', 'unquery']

from djapy.core.typing_utils import G_TYPE


class Schema(BaseModel):
    """
    Enhance to automatically detect many-to-many fields for serialization.
    """

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

    class Info:
        description: dict = {}


class unquery(Generic[G_TYPE]):
    pass
