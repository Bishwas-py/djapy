from pydantic import computed_field, Field
from djapy.schema import Schema, Form
from djapy.schema.schema import QueryList, Outsource


class TagSchema(Schema):
    id: int
    name: str


class ItemSchema(Schema):
    id: int
    title: str
    description: str
    price: float
    is_active: bool


class ItemDetailSchema(Outsource):
    id: int
    title: str
    description: str
    price: float
    is_active: bool
    tags: QueryList[TagSchema]

    @computed_field
    @property
    def tag_count(self) -> int:
        return len(self.tags)


class ItemCreateSchema(Schema):
    title: str
    description: str = ""
    price: float = Field(gt=0)
    is_active: bool = True


class ItemFormSchema(Form):
    title: str
    description: str = ""


class ErrorSchema(Schema):
    message: str
    alias: str = "error"
