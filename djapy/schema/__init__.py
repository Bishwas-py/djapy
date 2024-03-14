from typing import Generic, NewType, Type, TypeAlias, TypeVar

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


class Unquery:
    def __init__(self, type_: G_TYPE):
        self.unquery_type = type_


def unquery(type_: G_TYPE) -> G_TYPE:
    return Unquery(type_)
