# Data Input

As Djapy provides two approaches for basically everything; class based or function based, 
data input is also one of them. You can use either class based or function based approach
for taking data input from the client.

Here, we'll be discussing the function based approach.

## Input Decorators
We have primarily two decorators for taking inputs,
inputs can be defined as both payloads or the queries
sent by the client.

- @input_required
- @field_required

### @input_required

```python
from djapy.data.dec import input_required
```

This decorator accepts two types of inputs, data (payload)
and query. Any input passed inside `@input_required` 
is a strictly required field.

```python
@input_required(['title'])
```

Here, the `title` data is required by the client to
submit, if not provided it'll give a JSON error message
to the client.

```python
@input_required(
    ['title', 'author', 'category'],
    ['is_published', 'is_drafter']
)
def your_view_name(request, data, query):
    print(data.title, data.auther, data.category)
    print(query.is_published, query.is_drafter)
    ...
```

In the upper code, `title`, `author`, `category` are the
must required payloads, and `is_published` and `is_drafter
are the must required queries.

If you do not pass `data` or `query` in the `your_view_name`
you won't be able to get them via `data.data_name` or `query.query_name`.

> If you want to make anything optional while using
> `@input_required` you can use Django's `request.GET`. Or,
> you can use `@field_required`
 
 
### @field_required

```python
from djapy.data.dec import field_required
```

This decorator might be one of my fav input decorator, as it supports typing.
With `@field_required` you can use classes as input fields for both query or data.

```python
class Student:
    name: str
    age: int
    qualities: list
    weight: str|None

@field_required
def your_view_name(request, data=Student):
    print(data.name)
    print(data.age)
    print(data.qualities)
    print(data.weight)  # weight field in optional for client submission
    ...
```

Same as `@input_required` data and queries are optional to the `view_function`.

```python
class Mocca:
    flavour: str
    price: int
    coffee_type: str = 'latte'  # optional and default value
    consumer: str | None  # optional and None by default
    coffee_size: str | int # compulsory and dynamic type


@field_required
def your_view_name(request, query=Mocca):
    ...
```

#### Action flow
Both of the decorator return a `view_function` that has `request`, `data` (if  mentioned in params)
and `query` (if  mentioned in params) within its argument.