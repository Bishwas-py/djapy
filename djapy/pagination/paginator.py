from django.http import JsonResponse


class NumberPaginator:
    paginate_by: int = 25

    def get_paginate_by(self, request):
        return self.paginate_by

    def render(self, request):
        # Call render method if it has the same `render` superclass

        has_super_render = hasattr(super(), 'render')
        if has_super_render:
            super_render = getattr(super(), 'render')
            return super_render(request)

        queryset_func = getattr(self, 'get_queryset')
        queryset = queryset_func(request)

        # Manipulate queryset here

        jsonify = getattr(self, 'jsonify')
        data = jsonify(queryset)

        response = {
            'count': queryset.count(),
            'next': None,
            'previous': None,
            'results': data
        }
        return JsonResponse(response)
