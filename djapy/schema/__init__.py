import typing
from typing import Generic, NewType, Type, TypeAlias, TypeVar, Any

from pydantic import BaseModel, model_validator

__all__ = ['Schema', 'payload']

from pydantic_core.core_schema import ValidationInfo

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


class SourceAble(BaseModel):
    """
    Allows the model to have a source object.
    """
    _source_obj: Any | None = None
    _validation_info: ValidationInfo | None = None
    _context: dict | None = None

    @model_validator(mode="wrap")
    def __validator__(cls, val: Any, next_: typing.Callable[[Any], typing.Self],
                      validation_info: ValidationInfo) -> typing.Self:
        obj = next_(val)
        obj._source_obj = val
        obj._validation_info = validation_info
        obj._context = validation_info.context

        return obj


class Payload:
    def __init__(self, type_: G_TYPE):
        self.unquery_type = type_


def payload(type_: G_TYPE) -> G_TYPE:
    """
    Enforces any type to be received as a payload.
    """
    return Payload(type_)
