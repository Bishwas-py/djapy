__all__ = ['Schema', 'Outsource', 'QueryList', 'ImageUrl', 'get_json_dict', 'Form', 'QueryMapperSchema']

import inspect
import typing
from typing import Any, Annotated, List, Union, get_origin, ClassVar, Optional
from functools import lru_cache

from django.db.models import QuerySet
from django.db.models.fields.files import ImageFieldFile
from pydantic import (
    BaseModel,
    model_validator,
    model_serializer,
    ConfigDict,
    BeforeValidator,
    create_model,
    Json,
    TypeAdapter
)
from pydantic.functional_validators import field_validator
from pydantic_core.core_schema import ValidationInfo, SerializationInfo

from djapy.core import type_check
from djapy.core.labels import REQUEST_INPUT_DATA_SCHEMA_NAME, JSON_BODY_PARSE_NAME
from djapy.core.typing_utils import G_TYPE


class Schema(BaseModel):
   """
   Enhanced Schema with Pydantic V2 features:
   - Smart serialization with model_serializer
   - Performance optimizations with caching
   - Better Django ORM integration
   - Support for strict/lax validation modes
   """
   model_config = ConfigDict(
      validate_default=True,
      validate_assignment=True,
      from_attributes=True,
      arbitrary_types_allowed=True,
      # Performance: use attribute lookup instead of __dict__
      use_attribute_docstrings=True,
      # Better JSON schema generation
      json_schema_extra=lambda schema, model: schema.update(
         model.cvar_describe if hasattr(model, 'cvar_describe') else {}
      ),
   )
   cvar_c_type: ClassVar = "application/json"
   cvar_describe: ClassVar[dict] = {}  # Description for OpenAPI

   @classmethod
   @lru_cache(maxsize=128)
   def _get_type_adapter(cls) -> TypeAdapter:
      """Cached TypeAdapter for better performance."""
      return TypeAdapter(cls)

   @classmethod
   def validate_via_request(cls, json_data, context: Optional[dict] = None, strict: Optional[bool] = None):
      """
      Validate the model using request data with optional strict mode.
      
      Args:
          json_data: Data to validate
          context: Validation context
          strict: Enable strict validation (no coercion)
      """
      if single_schema := cls._single():
         single_schema_key, _ = single_schema
         json_data = {single_schema_key: json_data}

      return cls.model_validate(
         json_data,
         context=context or {},
         strict=strict
      )

   @classmethod
   @lru_cache(maxsize=32)
   def _single(cls) -> Optional[tuple[str, Any]]:
      """Cached check for single-field schema."""
      if len(cls.__annotations__) == 1:
         single_data_schema_obj = list(cls.__annotations__.values())[0]
         if type_check.schema_type(single_data_schema_obj):
            single_data_schema_key = list(cls.__annotations__.keys())[0]
            return single_data_schema_key, single_data_schema_obj
      return None

   @classmethod
   def single(cls) -> bool | tuple[str, Any]:
      """Check if schema has single field (for backwards compatibility)."""
      result = cls._single()
      return result if result else False

   @classmethod
   @lru_cache(maxsize=32)
   def is_empty(cls) -> bool:
      """Check if schema is empty (cached)."""
      return not cls.__annotations__

   @model_serializer(mode='wrap', when_used='json')
   def _serialize_for_json(self, serializer, info: SerializationInfo):
      """Custom JSON serialization with better Django ORM handling."""
      # Use default serialization but with optimizations
      data = serializer(self)
      
      # Handle Django-specific types that might need special serialization
      # This hook allows subclasses to customize serialization
      return self._post_serialize(data, info) if hasattr(self, '_post_serialize') else data

   def model_dump_fast(self, **kwargs) -> dict:
      """Fast model dump using mode='python' for internal use."""
      return self.model_dump(mode='python', **kwargs)

   def model_dump_json_optimized(self, **kwargs) -> str:
      """Optimized JSON serialization."""
      return self.model_dump_json(by_alias=True, exclude_none=True, **kwargs)


json_modal_schema = create_model(
   REQUEST_INPUT_DATA_SCHEMA_NAME,
   **{JSON_BODY_PARSE_NAME: (Json, ...)},
   __base__=Schema
)


def get_json_dict(to_jsonify_text: str):
   return json_modal_schema.model_validate({
      JSON_BODY_PARSE_NAME: to_jsonify_text
   }).dict().get(JSON_BODY_PARSE_NAME)


class QueryMapperSchema(Schema):
   """
   Multiple query or formdata like data can be validated using this model.
   """
   cvar_c_type = "_query_mapper"

   @field_validator("*", mode="before")
   def __field_validator__(cls, value: Any, info: ValidationInfo):
      field_type = cls.model_fields.get(info.field_name)
      origin = get_origin(field_type.annotation)
      if (inspect.isclass(origin) and issubclass(origin, typing.Iterable)
        and typing.get_args(field_type.annotation) != ()):
         return value
      if isinstance(value, list):  # Django's QueryDict {key: [value]} is converted to list.
         return value[0]
      return value


class Form(QueryMapperSchema):
   """
   Post form data can be validated using this model.
   """
   cvar_c_type = "application/x-www-form-urlencoded"


class Outsource(BaseModel):
   """
   Allows the model to have a source object, info object and context object.
   Specially useful for validation and checking on @computed_fields.
   """
   _obj = None
   _info: ValidationInfo = None
   _ctx: dict = None

   @model_validator(mode="wrap")
   def __validator__(cls,
                     val: Any,
                     next_: typing.Callable[[Any], typing.Self],
                     validation_info: ValidationInfo
                     ) -> typing.Self:
      obj = next_(val)
      obj._obj = val
      obj._info = validation_info
      obj._ctx = validation_info.context
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
