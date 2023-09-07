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
from django.views.decorators.csrf import csrf_exempt

from djapy.decs import djapy_view, model_to_json_node, node_to_json_response
from moko.models import Todo


def moko_post(request):
    todo = Todo.objects.first()
    todo.title = request.POST.get('title')
    todo.save()
    return todo


@djapy_view(['id', 'title', 'completed'], False)
def moko(request):
    return {
        'post': moko_post,
        'get': Todo.objects.all
    }


@csrf_exempt
@node_to_json_response
@model_to_json_node(['id', 'username'])
def moko_user(request):
    return request.user
```

Create RESTful APIs with Django Framework, without writing serializers, views, urls, etc. Or without bu11shi**s.


## License
[MIT](https://choosealicense.com/licenses/mit/)