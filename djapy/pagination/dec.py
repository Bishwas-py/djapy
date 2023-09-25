from functools import wraps

import django.core.handlers.wsgi
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.db.models import QuerySet

from djapy.wrappers.dec import object_to_json_node
from djapy.utils.models_parser import models_get_data, check_model_fields


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


def paginator_parser(
        model_fields: list | str = "__all__",
        exclude_null_fields: bool = False,
        object_parser: dict = None
):
    """
    :param model_fields: The fields to parse.
    :param exclude_null_fields: If True, the null fields will be excluded from the result.
    :param object_parser: The object parser, parses the object fields in the object list of the paginator.
    :return:
    """
    if object_parser is None:
        object_parser = {}
    field_parser = {
        'object_list': (models_get_data, dict(
            model_fields=model_fields,
            exclude_null_fields=exclude_null_fields,
            object_parser=object_parser)),
        'previous_page_number': previous_page_number_parser,
        'next_page_number': next_page_number_parser
    }
    n = object_to_json_node(
        object_fields=['number', 'object_list', 'has_next', 'has_previous', 'previous_page_number', 'next_page_number'],
        field_parser=field_parser,
        exclude_null_fields=exclude_null_fields
    )
    return n


def get_paginated_data(queryset: QuerySet, page: int, page_size: int | str = 10):
    if type(page_size) == str:
        if page_size == 'all':
            return queryset.all()
        elif page_size.isdigit():
            page_size = int(page_size)
        else:
            page_size = 10

    paginator = Paginator(queryset, page_size)  # Create paginator with todos and specify number of todos per page

    try:
        page_data = paginator.page(page)
    except PageNotAnInteger:  # If page is not an integer, deliver first page
        page_data = paginator.page(1)
    except EmptyPage:  # If page is out of range (e.g. 9999), deliver last page of results
        page_data = paginator.page(paginator.num_pages)

    return page_data


def djapy_paginator(fields: list[str] | str, exclude_null_fields=True, object_parser=None):
    if object_parser is None:
        object_parser = {}

    if not callable(fields):
        check_model_fields(fields)
    paginator_parser_func = paginator_parser(fields, exclude_null_fields, object_parser)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: 'django.core.handlers.wsgi.WSGIRequest', *args, **kwargs):
            page_size = request.GET.get('page_size', 10)
            page = request.GET.get('page', 1)

            # Get the queryset from the original function
            view_func_or_queryset = view_func(request, *args, **kwargs)
            if isinstance(view_func_or_queryset, QuerySet):
                paginated_data = get_paginated_data(view_func_or_queryset, page, page_size)
                return paginator_parser_func(paginated_data)(request, *args, **kwargs)
            return view_func_or_queryset

        return _wrapped_view

    return decorator
