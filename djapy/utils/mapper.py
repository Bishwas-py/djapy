from django.db import models
from django.db.models import QuerySet
from django.http import JsonResponse

from djapy.utils.models_parser import models_get_data
from djapy.utils import defaults
import djapy.utils.types


class DjapyModelJsonMapper:
    GLOBAL_FIELDS = defaults.GLOBAL_FIELDS
    __EXCLUDE_NULL_FIELDS = False
    __OPEN_MODE = '__open__'

    def __init__(self, model_objects, model_fields: str | list | tuple[str, list],
                 **kwargs: "djapy.utils.types.JsonNodeParams") -> None:
        self.model_objects = model_objects
        self.model_fields = model_fields
        self.exclude_null_fields = kwargs.get('exclude_null_fields', self.__EXCLUDE_NULL_FIELDS)

    def get_model_object_name(self):
        if isinstance(self.model_objects, models.Model):
            return self.model_objects.__class__.__name__
        elif isinstance(self.model_objects, QuerySet):
            return self.model_objects.model.__name__
        else:
            return "Unknown Model Object"

    def result_data(self):
        return models_get_data(self.model_objects, self.model_fields, self.exclude_null_fields)

    def nodify(self) -> JsonResponse:
        return JsonResponse(self.result_data(), safe=False)


class DjapyObjectJsonMapper:
    def __init__(self, raw_object, object_fields: set | list | str,
                 exclude_null_fields: bool = False,
                 field_parser: "djapy.utils.types.FieldParserType" = None) -> None:
        self.raw_object = raw_object
        self.object_fields = object_fields
        self.exclude_null_fields = exclude_null_fields
        self.field_parser = field_parser

    def nodify(self) -> JsonResponse:
        if isinstance(self.raw_object, object):
            result_data = {
            }
            for field in self.object_fields:
                if isinstance(self.raw_object, dict):
                    object_field_value = self.raw_object.get(field, None)
                else:
                    object_field_value = getattr(self.raw_object, field, None)

                # Apply field parser if exists
                if self.field_parser and field in self.field_parser:
                    _field_parser = self.field_parser[field]
                    if isinstance(_field_parser, tuple):
                        if not callable(_field_parser[0]):
                            raise TypeError(f"Field parser must be a callable. Got {_field_parser[0]}")
                        func_args_kwargs = _field_parser[1:]
                        args = []
                        kwargs = {}
                        for args_kwargs in func_args_kwargs:
                            if isinstance(args_kwargs, dict):
                                kwargs = args_kwargs
                            elif isinstance(args_kwargs, tuple):
                                args = args_kwargs
                            elif isinstance(args_kwargs, list):
                                args = (args_kwargs,)
                        object_field_value = _field_parser[0](object_field_value, *args, **kwargs)
                    else:
                        object_field_value = _field_parser(object_field_value)
                    field_name = field
                elif callable(object_field_value):
                    object_field_value = object_field_value()
                    field_name = field.replace('get_', '')
                else:
                    field_name = field

                if not self.exclude_null_fields or object_field_value is not None:
                    result_data[field_name] = object_field_value

            return JsonResponse(result_data)
        else:
            raise ValueError("Invalid input type. Must be an object.")
