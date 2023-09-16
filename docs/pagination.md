# Pagination

With Djapy, you can implement Django like pagination easily. The paginator class should
always be placed after the DjapyView. 

To implement the pagination, you need to declare the `get_queryset` method.

## Pagination Decorator

```python
from djapy.pagination.dec import djapy_paginator
```

This decorator can be used to paginate the queryset. The decorator takes two arguments:
`fields` and `exclude_null_fields`. The `fields` argument is a list of fields to be
included in the response. The `exclude_null_fields` argument is a boolean value, which
when set to `True` will exclude the fields with `null` values from the response.

```python
@djapy_paginator(['id', 'title', 'will_be_completed_at', 'created_at'])
def your_view_function(request):
    model = Todo.objects.all()
    return model
```

You can set `page_size` and `page` in request query params to paginate the queryset.

## Number pagination
Use the `NumberPaginator` class.

```python
from djapy.views.generics import DjapyView
from djapy.pagination.paginator import NumberPaginator

from moco.models import Blog


class MyBlogsView(DjapyView, NumberPaginator):
    model_fields = '__all__'
    paginate_by = 10  # You can change this

    def get_queryset(self, request):
        model = Blog.objects.all()
        return model
```

