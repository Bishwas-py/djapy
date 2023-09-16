## Djapy - Django Framework is enough
Djapy is a simple Django library that provides complete control to the developers to instantly
create restful APIs with minimal code. It is a simple library that provides a set of classes
and decorators that can be used to create restful APIs.

## Installation
```bash
pip install djapy
```

## Usage

```python
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from djapy.decs import djapy_model_view, node_to_json_response
from djapy.auth.dec import djapy_login_required
from djapy.data.dec import field_required, input_required
from djapy.decs import djapy_paginator
from .models import Todo


@djapy_login_required
@input_required(['title'])
def todo_post(request, data, *args, **kwargs):
    will_be_completed_at = request.POST.get('will_be_completed_at')
    todo = Todo.objects.create(
        title=data.title,
        will_be_completed_at=will_be_completed_at,
        user_id=request.user.id
    )
    return todo


@djapy_paginator(['id', 'title', 'will_be_completed_at', 'created_at', 'user_id', 'username'])
def todo_get(request, *args, **kwargs):
    todos = Todo.objects.all()
    todos = todos.filter(user=request.user)
    return todos


class TodoPathData:
    id: int
    title: str | None = None
    will_be_completed_at: str | None = None
    is_completed: bool | None = None


@djapy_login_required
@field_required
def todo_patch(request, data: TodoPathData, *args, **kwargs):
    todo = Todo.objects.get(id=data.id)
    todo.title = data.title if data.title else todo.title
    todo.will_be_completed_at = data.will_be_completed_at if data.will_be_completed_at else None
    todo.completed_at = timezone.now() if data.is_completed else todo.completed_at
    todo.save()
    return todo


@csrf_exempt
@djapy_login_required
@djapy_model_view(['id', 'title', 'will_be_completed_at', 'created_at'], True)
def todo_view(request):
    return {
        'post': todo_post,
        'get': todo_get,
        'patch': todo_patch
    }


@csrf_exempt
@node_to_json_response
@input_required(['username', 'password'])
def login_for_session(request, data, *args, **kwargs):
    user = authenticate(username=data.username, password=data.password)
    if user:
        login(request, user)
    return JsonResponse({
        'session_key': request.session.session_key,
        'is_authenticated': user.is_authenticated if user else False,
        'expiry_age': request.session.get_expiry_age(),
        'csrf_token': request.COOKIES.get('csrftoken'),
        'id': user.id if user else None,
    })


class ExampleAPIView(DjapyView):
    model_fields = '__all__'

    def get_queryset(self, request):
        model = Todo.objects.all()
        return model


class ProtectedAPIView(LoginRequiredMixin, DjapyView):
    model_fields = '__all__'

    def get_queryset(self, request):
        model = Todo.objects.all()
        return model
```

Create RESTful APIs with Django Framework, without writing serializers, views, urls, etc. Or without bu11shi**s.


## License
[MIT](https://choosealicense.com/licenses/mit/)
