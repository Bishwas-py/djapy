# Data wrappers

Data modifiers are set of decorator that convert specific type
of data to another specific type of data.

## @model_to_json_node

```python
from djapy.wrappers.dec import model_to_json_node
```

This decorator convert any model returned by the `view_fuction` to 
a `JSON Node` type. `JSON Node` is a data type that contains 
parsed JSON data within itself.

```python
from your_app_name.models import Todo
def all_todos_view(request):
    todo = Todo.objects.all()
    return todo
# or

def first_todo_view(request):
    todo = Todo.objects.first()
    return todo
```

On the both upper returned model queryset or model objects, you can
convert them to JSON node, by using `@model_to_json_node`.

```python
@model_to_json_node(['title', 'is_completed'], is_strictly_bounded=False)
def your_view_func(request):
    your_object_or_query = Todo.objects.all() # or one object
    retrun your_object_or_query
```

The returned data for queryset will be a list, and for model object, it'll
be a JSON object. `is_strictly_bounded` if set to True, it removes all
the `null` or `None` value from the JSON node.

`model_to_json_node` is not alone compatible for converting JSON node to
JSON response, you have to use `node_to_json_response` for as a final decorator.

### Action flow

`@model_to_json_node` returns `DjapyModelJsonMapper`'s object as after all executions.

## @node_to_json_response

```python
from djapy.wrappers.dec import node_to_json_response
```

This decorator is used as final decorator to convert `JSON node` to actual JSON Response.

```python
@node_to_json_response
@model_to_json_node(['title', 'is_completed'], is_strictly_bounded=False)
def your_view_func(request):
    your_object_or_query = Todo.objects.all() # or one object
    retrun your_object_or_query
```

It might be something like this in client's side:

```json
[
  {
    "title": "Todo title",
    "is_completed": true
  },
  {
    "title": "Todo title #2",
    "is_completed": false
  }
  ...
]
```
If one object (`todo_object`) was sent, it would be something like:
```json
{
  "title": "Todo title",
  "is_completed": true
}
```
That's it. 

### Action flow

`node_to_json_response` returns a `JsonResponse`'s object after all execution. This make
the serialized data possible.

## @object_to_json_node

```python
from djapy.wrappers.dec import object_to_json_node
```

This decorator is used to convert any object to JSON node. It's not only for model
objects, but also for any object. Let it be a `dict` or a class object.

```python
@object_to_json_node(['title', 'is_completed'])
def your_view_func(request):
    your_object = {
        'title': 'Todo title',
        'is_completed': True
    }
    return your_object

# or

class Todo:
    title: str
    is_completed: bool

@object_to_json_node(['title', 'is_completed'])
def your_view_func(request):
    your_object = Todo()
    your_object.title = 'Todo title'
    your_object.is_completed = True
    return your_object
```

### Action flow

`object_to_json_node` returns `DjapyObjectJsonMapper`'s object after all execution.