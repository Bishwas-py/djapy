from typing import Generic, TypeVar

from pydantic import BaseModel


class Schema(BaseModel):
    """
    Enhance to automatically detect many-to-many fields for serialization.
    """

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True
        is_query = False

    class Info:
        description: dict = {}
