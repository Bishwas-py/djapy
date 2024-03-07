from pydantic import BaseModel

__all__ = ['Schema', 'unquery']


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


class unquery:
    """
    Distracts query params from getting into query params, and makes them data/payload
    """
    pass
