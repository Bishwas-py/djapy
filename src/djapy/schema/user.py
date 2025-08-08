from pydantic import field_validator

from djapy.schema import Schema


class PermissionSchema(Schema):
   codename: str
   name: str


class UserSchema(Schema):
   id: int
   username: str
   user_permissions: list[PermissionSchema]
   first_name: str
   last_name: str

   @field_validator('user_permissions', mode='before')
   def validate_user_permissions(cls, value):
      all_permissions = value.all()
      return all_permissions
