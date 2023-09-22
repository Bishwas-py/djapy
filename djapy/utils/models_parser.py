from django.db import models

from djapy.utils import defaults


def check_model_fields(model_fields):
    """
    Checks if the model fields are valid.
    :param model_fields: The model fields to check.
    :return bool: True if the model fields are valid, False otherwise.
    :raises ValueError: If the model fields are not valid.
    """
    if isinstance(model_fields, str):
        if model_fields == defaults.ALL_FIELDS:
            return True
        raise ValueError(f"Model fields must be a list or '{defaults.ALL_FIELDS}'")
    if isinstance(model_fields, (list, tuple, set)):
        if all(isinstance(field, str) for field in model_fields):
            return True
    raise ValueError(f"Model fields must be a list or '{defaults.ALL_FIELDS}'")


def model_get_fields(model_objects: models.QuerySet | models.Model,
                     model_fields: list | str,
                     is_strictly_bounded: bool = False):
    temp_fields = []
    concatenated_fields = []

    if check_model_fields(model_fields):
        if model_fields == defaults.ALL_FIELDS:
            if isinstance(model_objects, models.Model):
                temp_fields = [field.name for field in model_objects._meta.fields]
            elif isinstance(model_objects, models.QuerySet):
                temp_fields = [field.name for field in model_objects.model._meta.fields]

            if not is_strictly_bounded:
                concatenated_fields = defaults.GLOBAL_FIELDS
        else:
            temp_fields = model_fields

        temp_fields += concatenated_fields

        if is_strictly_bounded:
            temp_fields = [field for field in temp_fields if field is not None]

        return temp_fields

    return temp_fields


def models_get_data(model_objects: models.QuerySet | models.Model,
                    model_fields: list | str,
                    is_strictly_bounded: bool = False,
                    object_parser=None):
    if object_parser is None:
        object_parser = {}
    final_fields = model_get_fields(model_objects, model_fields, is_strictly_bounded)

    if isinstance(model_objects, models.Model):
        result = {}
        for field in final_fields:
            if field in object_parser:
                result[field] = object_parser[field](model_objects)
            else:
                result[field] = getattr(model_objects, field, None)
        return result

    elif isinstance(model_objects, models.QuerySet):
        result = []
        for obj in model_objects:
            temp = {}
            for field in final_fields:
                if field in object_parser:
                    temp[field] = object_parser[field](obj)
                else:
                    temp[field] = getattr(obj, field, None)
            result.append(temp)
        return result

    else:
        return {}
