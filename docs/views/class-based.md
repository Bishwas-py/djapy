# Djapy using class based views

It's easy to create REST API with Djapy using class based views. With Djapy, you don't
need to write your serializer.

## Quick API example

Here's how you can make your API endpoint from the model.

```python
from djapy.views.generics import DjapyView
from your_app_name.models import Blog


class BlogListView(DjapyView):
    model_fields = '__all__'

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

## Protect your API view?
Djapy by default provides LoginRequiredMixin, AllowSuperuserMixin.
Here's how you can only allow your API access to the logged-in users.
Keep LoginRequiredMixin always at the beginning.

```python
from djapy.views.generics import DjapyView
from djapy.mixins.permissions import LoginRequiredMixin

from your_app_name.models import Blog


class ProtectedAPIView(LoginRequiredMixin, DjapyView):
    model_fields = '__all__'

    def get_queryset(self, request):
        model = Blog.objects.get_queryset()
        return model
```

If you need to manage more permission and controls, 
you can extend the PermissionMixin class from `djapy.mixins.permission.PermissionMixin` class to protect your view.

