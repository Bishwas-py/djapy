from pydantic import field_validator

from djapy.schema import Schema


class Permission(Schema):
    codename: str
    name: str


class User(Schema):
    id: int
    username: str
    user_permissions: list[Permission]

    @field_validator('user_permissions', mode='before')
    def validate_user_permissions(cls, value):
        all_permissions = value.all()
        return all_permissions
