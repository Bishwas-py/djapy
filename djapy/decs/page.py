from django.core.paginator import EmptyPage

from djapy.decs.wrappers import object_to_json_node
from djapy.parser.models_parser import models_get_data


def previous_page_number_parser(page_obj):
    try:
        return page_obj()
    except EmptyPage:
        return None


def next_page_number_parser(page_obj):
    try:
        return page_obj()
    except EmptyPage:
        return None


def djapy_paginator(fields: list[str] | str = "__all__", exclude_null_fields=True):
    """
    The djapy_paginator decorator transforms the data returned by a function into a paginated JsonResponse.

    :param fields: A list of strings or a string representing the field names to be used in the 'object_list'.
                   Default is "__all__", which includes all model fields. Field names are case-sensitive.
    :param exclude_null_fields: If True, the fields with null values are excluded from the JsonResult. Default is True.

    The function parses the data of the Django paginator into a JsonResult with the following keys:
    - 'number': The page number.
    - 'object_list': A list of objects with the fields passed in the fields parameter.
    - 'has_next': A boolean indicating whether a next page exists.
    - 'has_previous': A boolean indicating whether a previous page exists.
    - 'previous_page_number': The number of the previous page, if it exists. Otherwise, will be excluded if exclude_null_fields is True.
    - 'next_page_number': The number of the next page, if it exists. Otherwise, will be excluded if exclude_null_fields is True.
    """
    field_parser = {
        'object_list': (models_get_data, {'model_fields': fields}),
        'previous_page_number': previous_page_number_parser,
        'next_page_number': next_page_number_parser
    }
    return object_to_json_node(
        ['number', 'object_list', 'has_next', 'has_previous', 'previous_page_number', 'next_page_number'],
        field_parser,
        exclude_null_fields=exclude_null_fields
    )
