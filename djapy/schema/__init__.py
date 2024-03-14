from typing import Generic, NewType, Type, TypeAlias, TypeVar

from pydantic import BaseModel

__all__ = ['Schema', 'payload']

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


class Payload:
    def __init__(self, type_: G_TYPE):
        self.unquery_type = type_


def payload(type_: G_TYPE) -> G_TYPE:
    """
    Enforces any type to be received as a payload.
    """
    return Payload(type_)
