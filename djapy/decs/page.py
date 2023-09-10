from functools import wraps

import django.core.handlers.wsgi
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger

from djapy.decs.wrappers import object_to_json_node
from djapy.parser.models_parser import models_get_data, check_model_fields


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


def paginator_parser(fields: list[str] | str = "__all__", exclude_null_fields=True):
    field_parser = {
        'object_list': (models_get_data, {'model_fields': fields}),
        'previous_page_number': previous_page_number_parser,
        'next_page_number': next_page_number_parser
    }
    n = object_to_json_node(
        ['number', 'object_list', 'has_next', 'has_previous', 'previous_page_number', 'next_page_number'],
        field_parser,
        exclude_null_fields=exclude_null_fields
    )
    return n


def djapy_paginator(fields: list[str] | str, exclude_null_fields=True):
    if not callable(fields):
        check_model_fields(fields)
    paginator_parser_func = paginator_parser(fields, exclude_null_fields)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: 'django.core.handlers.wsgi.WSGIRequest', *args, **kwargs):
            page_size = request.GET.get('page_size', 10)
            page = request.GET.get('page', 1)

            # Get the queryset from the original function
            queryset = view_func(request, *args, **kwargs)

            if type(page_size) == str:
                if page_size == 'all':
                    return queryset.all()
                elif page_size.isdigit():
                    page_size = int(page_size)
                else:
                    page_size = 10

            paginator = Paginator(queryset,
                                  page_size)  # Create paginator with todos and specify number of todos per page

            try:
                page_data = paginator.page(page)
            except PageNotAnInteger:  # If page is not an integer, deliver first page
                page_data = paginator.page(1)
            except EmptyPage:  # If page is out of range (e.g. 9999), deliver last page of results
                page_data = paginator.page(paginator.num_pages)

            return paginator_parser_func(page_data)(request, *args, **kwargs)

        return _wrapped_view

    return decorator
