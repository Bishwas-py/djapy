from django.db import models
from django.db.models import QuerySet
from django.http import JsonResponse

from djapy.utils.types import JsonNodeParams

__ALL_FIELDS = '__all__'


def check_model_fields(model_fields):
    """
    Checks if the model fields are valid.
    :param model_fields: The model fields to check.
    :return bool: True if the model fields are valid, False otherwise.
    :raises ValueError: If the model fields are not valid.
    """
    if isinstance(model_fields, str):
        if model_fields == __ALL_FIELDS:
            return True
        raise ValueError(f"Model fields must be a list or '{__ALL_FIELDS}'")
    if isinstance(model_fields, (list, tuple, set)):
        if all(isinstance(field, str) for field in model_fields):
            return True
    raise ValueError(f"Model fields must be a list or '{__ALL_FIELDS}'")


class DjapyModelJsonMapper:
    GLOBAL_FIELDS = ['id', 'created_at', 'updated_at']
    __IS_STRICTLY_BOUNDED = False
    __OPEN_MODE = '__open__'

    def __init__(self, model_objects, model_fields: str | list | tuple[str, list],
                 **kwargs: JsonNodeParams) -> None:
        self.model_objects = model_objects
        self.model_fields = model_fields
        self.is_strictly_bounded = kwargs.get('is_strictly_bounded', self.__IS_STRICTLY_BOUNDED)

    def get_final_fields(self) -> iter:
        temp_fields = self.model_fields
        concatenated_fields = []

        if check_model_fields(self.model_fields):
            if isinstance(self.model_objects, models.Model):
                temp_fields = [field.name
                               for field in self.model_objects._meta.fields]
                concatenated_fields = [] if self.is_strictly_bounded else self.GLOBAL_FIELDS
            elif isinstance(self.model_objects, QuerySet):
                temp_fields = [field.name
                               for field in self.model_objects.model._meta.fields]
                concatenated_fields = [] if self.is_strictly_bounded else self.GLOBAL_FIELDS

        return temp_fields + concatenated_fields

    def get_model_object_name(self):
        if isinstance(self.model_objects, models.Model):
            return self.model_objects.__class__.__name__
        elif isinstance(self.model_objects, QuerySet):
            return self.model_objects.model.__name__
        else:
            return "Unknown Model Object"

    def nodify(self) -> JsonResponse:
        final_fields = self.get_final_fields()
        if isinstance(self.model_objects, models.Model):
            json_node = {
                field: getattr(self.model_objects, field, None) for field in final_fields
            }
            return JsonResponse(json_node)
        elif isinstance(self.model_objects, QuerySet):
            result = [
                {
                    field: getattr(obj, field, None) for field in final_fields
                }
                for obj in self.model_objects
            ]
            return JsonResponse(result, safe=False)
        else:
            raise ValueError("Invalid input type. Must be a Model or QuerySet.")


class DjapyObjectJsonMapper:
    def __init__(self, raw_object, object_fields: set | list | str,
                 exclude_null_fields: bool = False, field_parser: dict = None, **kwargs: JsonNodeParams) -> None:
        self.raw_object = raw_object
        self.object_fields = object_fields
        self.exclude_null_fields = exclude_null_fields
        self.field_parser = field_parser

    def nodify(self) -> JsonResponse:
        if isinstance(self.raw_object, object):
            json_node = {
            }
            for field in self.object_fields:
                if isinstance(self.raw_object, dict):
                    usable_object = self.raw_object.get(field, None)
                else:
                    usable_object = getattr(self.raw_object, field, None)

                # Apply field parser if exists
                if self.field_parser and field in self.field_parser:
                    usable_object = self.field_parser[field](usable_object)
                    field_name = field
                elif callable(usable_object):
                    usable_object = usable_object()
                    field_name = field.replace('get_', '')
                else:
                    field_name = field

                if not self.exclude_null_fields or usable_object is not None:
                    json_node[field_name] = usable_object

            return JsonResponse(json_node)
        else:
            raise ValueError("Invalid input type. Must be an object.")
