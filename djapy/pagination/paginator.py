from djapy.pagination.dec import paginator_parser, get_paginated_data
import djapy.utils.mapper as djapy_mapper


class NumberPaginator:
    page: int = 1
    page_size: str | int = 25

    def get_paginator_parser_func(self):
        model_fields = getattr(self, 'model_fields')
        exclude_null_fields = getattr(self, 'exclude_null_fields')
        return paginator_parser(model_fields, exclude_null_fields)

    def get_paginate_by(self, request):
        page = request.GET.get('page', self.page)
        page_size = request.GET.get('page_size', self.page_size)
        return page, page_size


    def render(self, request, *args, **kwargs):
        # Call render method if it has the same `render` superclass

        has_super_render = hasattr(super(), 'render')
        if has_super_render:
            super_render = getattr(super(), 'render')
            return super_render(request)

        queryset_func = getattr(self, 'get_queryset')
        queryset = queryset_func(request)

        # Manipulate queryset here

        page, page_size = self.get_paginate_by(request)
        paginated_data = get_paginated_data(queryset, page, page_size)
        paginator_parser_func = self.get_paginator_parser_func()
        json_map: 'djapy_mapper.DjapyObjectJsonMapper' = paginator_parser_func(paginated_data)(request, *args, **kwargs)
        return json_map.nodify()  # nodify() returns a JsonResponse,
