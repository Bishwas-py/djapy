__all__ = ['Schema', 'SourceAble']

import typing
from typing import Any
from pydantic import BaseModel, model_validator, ConfigDict
from pydantic_core.core_schema import ValidationInfo


class Schema(BaseModel):
    """
    Enhance to automatically detect many-to-many fields for serialization.
    """
    model_config = ConfigDict(validate_default=True, validate_assignment=True, from_attributes=True,
                              arbitrary_types_allowed=True)

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
