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
                     include_global_field: bool = False):
    """
    Gets the model fields.
    :param model_objects: The model objects.
    :param model_fields: The model fields.
    :param include_global_field: Boolean value to indicate whether the model fields are strictly bounded,
    i.e. no extra fields are allowed mentioned in defaults.GLOBAL_FIELDS. [i.e. 'id', 'created_at' and 'updated_at']
    """
    temp_fields = []

    if check_model_fields(model_fields):
        if model_fields == defaults.ALL_FIELDS:
            if isinstance(model_objects, models.Model):
                temp_fields = [field.name for field in model_objects._meta.fields]
            elif isinstance(model_objects, models.QuerySet):
                temp_fields = [field.name for field in model_objects.model._meta.fields]
        else:
            temp_fields = model_fields

        if include_global_field:
            temp_fields += defaults.GLOBAL_FIELDS

    return temp_fields


def models_get_data(model_objects: models.QuerySet | models.Model,
                    model_fields: list | str,
                    include_global_field: bool = False,
                    exclude_null_fields: bool = True,
                    object_parser=None,
                    ):
    """
    Gets the model data.
    :param model_objects: The model objects.
    :param model_fields: The model fields, list or __all__.
    :param include_global_field: Boolean value to indicate whether the model fields are strictly bounded,
    i.e. no extra fields are allowed mentioned in `defaults.GLOBAL_FIELDS`, if True.
    [This attribute is not exclude_null_fields]
    :param exclude_null_fields: Boolean value to indicate whether null fields should be excluded, removes fields with
    value None if True.
    :param object_parser: A dictionary of field parsers to apply to the object fields.
    """
    if object_parser is None:
        object_parser = {}

    final_fields = model_get_fields(
        model_objects=model_objects,
        model_fields=model_fields,
        include_global_field=include_global_field
    )
    print(final_fields)

    if isinstance(model_objects, models.Model):
        result = {}
        for field in final_fields:
            if field in object_parser:
                field_value = object_parser[field](model_objects)
            else:
                field_value = getattr(model_objects, field, None)
            if exclude_null_fields and field_value is None:
                continue
            result[field] = field_value
        return result

    elif isinstance(model_objects, models.QuerySet):
        result = []
        for obj in model_objects:
            temp = {}
            for field in final_fields:
                if field in object_parser:
                    field_value = object_parser[field](obj)
                else:
                    field_value = getattr(obj, field, None)
                if exclude_null_fields and field_value is None:
                    continue
                temp[field] = field_value
            result.append(temp)
        return result
    else:
        return {}
