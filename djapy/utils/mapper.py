from django.db import models
from django.db.models import QuerySet
from django.http import JsonResponse

from djapy.utils.models_parser import models_get_data
from djapy.utils import defaults
import djapy.utils.types


class DjapyModelJsonMapper:
    def __init__(self,
                 model_objects,
                 model_fields: list | str,
                 exclude_null_fields: bool = False,
                 include_global_field: bool = True,
                 object_parser: "djapy.utils.types.FieldParserType" = None) -> None:
        if isinstance(model_objects, tuple) and len(model_objects) == 2:
            self.model_objects, self.status_code = model_objects
        else:
            self.model_objects = model_objects
            self.status_code = 200

        self.model_fields = model_fields
        self.include_global_field = include_global_field
        self.exclude_null_fields = exclude_null_fields
        self.object_parser = object_parser

    def get_model_object_name(self):
        if isinstance(self.model_objects, models.Model):
            return self.model_objects.__class__.__name__
        elif isinstance(self.model_objects, QuerySet):
            return self.model_objects.model.__name__
        else:
            return "Unknown Model Object"

    def result_data(self):
        return models_get_data(
            model_objects=self.model_objects,
            model_fields=self.model_fields,
            include_global_field=self.include_global_field,
            exclude_null_fields=self.exclude_null_fields,
            object_parser=self.object_parser
        )

    def nodify(self) -> JsonResponse:
        return JsonResponse(self.result_data(), safe=False, status=self.status_code)


class DjapyObjectJsonMapper:
    def __init__(self, raw_object, object_fields: set | list | str,
                 exclude_null_fields: bool = False,
                 field_parser: "djapy.utils.types.FieldParserType" = None) -> None:
        if isinstance(raw_object, tuple) and len(raw_object) == 2:
            self.raw_object, self.status_code = raw_object
        else:
            self.raw_object = raw_object
            self.status_code = 200

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

            return JsonResponse(result_data, safe=False, status=self.status_code)
        else:
            raise ValueError("Invalid input type. Must be an object.")
