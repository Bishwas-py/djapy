# Getting started

I assume you have Django, and it's son `Djapy` installed already. And you have created a project
using `django-admin startproject <project_name>`.

## Writing your first API

Let's create a simple API that returns a list of paginated data from a model.

First, create a new app using `python manage.py startapp <app_name>`. Then, add the app to your `INSTALLED_APPS`
in `settings.py`.

Now, create a new model in `models.py`:

```python
from django.db import models


class Todo(models.Model):
    title = models.CharField(max_length=100)
    completed_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    will_be_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
```

Now, go to `views.py` and add the following code:

```python
from django.views.decorators.csrf import csrf_exempt

from djapy.views.dec import djapy_model_view
from djapy.auth.dec import djapy_login_required
from djapy.data.dec import input_required
from djapy.pagination.dec import djapy_paginator
from .models import Todo


@djapy_login_required
@input_required(['title'])
def todo_post(request, data, query, *args, **kwargs):
    will_be_completed_at = request.POST.get('will_be_completed_at')
    todo = Todo.objects.create(
        title=data.title,
        will_be_completed_at=will_be_completed_at
    )
    return todo


@djapy_paginator(['id', 'title', 'will_be_completed_at', 'created_at'])
def todo_get(request, *args, **kwargs):
    todos = Todo.objects.all()
    return todos


@csrf_exempt
@djapy_login_required
@djapy_model_view(['id', 'title', 'will_be_completed_at', 'created_at'], True)
def todo_view(request):
    return {
        'post': todo_post,
        'get': todo_get
    }

```

If you like to use a class based view, you need to import DjapyView
```python

from djapy.views.generics import DjapyView


class TodoView(DjapyView):
    def get(self, request):
        return {
            'message': 'Hello from GET request'
        }

    def post(self, request):
        return {
            'message': 'Hello from POST request'
        }
```
To learn more, see Djapy [class based view](views.md) section.

Now, go to `urls.py` and add the following code:

```python
from django.urls import path
from .views import todo_view

urlpatterns = [
    path('', todo_view, name='app-name-action'),
    
    # For class based view
    path('class-example/', TodoView.as_view(), name='todo_view')
]
```

Now, run `python manage.py migrate` to create the database tables. And
run `python manage.py runserver` to start the server.

Now, go to `http://localhost:8000/` to see the API in action.

## What's next?

You can continue reading the documentation, [data and queries handlers...](data-input.md)