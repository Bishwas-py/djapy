from pydantic import BaseModel


class Schema(BaseModel):
    """
    Enhance to automatically detect many-to-many fields for serialization.
    """

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

