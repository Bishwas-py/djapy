# Pagination

With Djapy, you can implement Django like pagination easily. The paginator class should
always be placed after the DjapyView. 

To implement the pagination, you need to declare the `get_queryset` method.

## Number pagination
Use the `NumberPaginator` class.

```python
from djapy.pagination.paginator import NumberPaginator
from djapy.views.generics import DjapyView

from moco.models import Blog


class MyBlogsView(DjapyView, NumberPaginator):
    model_fields = '__all__'
    paginate_by = 10  # You can change this

    def get_queryset(self, request):
        model = Blog.objects.all()
        return model
```

