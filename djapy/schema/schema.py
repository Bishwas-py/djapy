__all__ = ['Schema', 'SourceAble', 'QueryList']

import typing
from typing import Any, Annotated, List, Union

from django.db.models import QuerySet
from django.db.models.fields.files import ImageFieldFile
from pydantic import BaseModel, model_validator, ConfigDict, BeforeValidator
from pydantic_core.core_schema import ValidationInfo

from djapy.core.typing_utils import G_TYPE


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


def query_list_validator(value: QuerySet):
    """
    Validator to ensure the Django QuerySet is converted to an iterable.
    """
    return value.all()


QueryList = Annotated[List[G_TYPE], BeforeValidator(query_list_validator)]


def image_field_file_validator(value: ImageFieldFile):
    """
    Validator to ensure the ImageFieldFile is converted to a URL.
    """
    if value:
        return value.url
    return None


ImageUrl = Annotated[Union[None, str], BeforeValidator(image_field_file_validator)]
