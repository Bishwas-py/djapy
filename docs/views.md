# Djapy using class based views

It's easy to create REST API with Djapy using class based views. With Djapy, you don't
need to write your serializer.

## Quick API example

Here's how you can make your API endpoint from the model.

```python
from djapy.views.generics import DjapyView
from your_app_name.models import Blog


class BlogListView(DjapyView):
    model_fields = ['pk', 'title', 'description'] # Use '__all__' to include all fields

    def get_queryset(self, request):
        model = Blog.objects.all()
        return model

```

You can also specify your fields like this `model_fields = ['pk', 'date_created', 'title', 'content']` .
The `get_queryset` methods expects the QuerySet object.

## Want to separate method for GET/POST request?

Djapy supports Django's like separate `get`, `post` methods. If you want `update`, `path` or any other method,
you can also write it like this `def requestMethodName(self, request)`.

```python
from django.http import JsonResponse
from djapy.views.generics import DjapyView


class ExampleAPIView(DjapyView):

    def get(self, request):
        return {
            'name': 'Djapy on GET'
        }

    def post(self, request):
        return {
            'name': 'Djapy on POST'
        }


class CreateAPIView(DjapyView):
    def post(self, request):
        # perform 

        return JsonResponse(data={
            'status': 'success'
        }, status=201)
```
