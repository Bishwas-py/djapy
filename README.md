# Introduction

This is the documentation for the `Djapy` library, which is designed to let you make RESTful APIs
within Django with no boilerplate, using plain Python and Django.

Djapy is molded according to `Django`'s philosophy of "batteries included", and is designed to
be as simple as possible to use, while still being powerful enough to handle most use cases.

> We believe in "Do not use a Framework inside an awesome Framework".

It does not enforce any particular design pattern, and is designed to be as flexible as possible,
while still being easy to use.

## Installation

Djapy is available on PyPI, and can be installed with `pip`:

```bash
pip install djapy
```

## Basic Rest API

```python
from djapy.pagination.dec import djapy_paginator


@djapy_paginator([
    'id', 'title', 'will_be_completed_at', 'created_at',
    'username', 'completed_at'
])
def todo_get(request, *args, **kwargs):
    todos = Todo.objects.all()
    todos = todos.filter(user=request.user).order_by('-completed_at')
    return todos
```

## Creating a new project

To create a new project, run the following command:

```bash
django-admin startproject <project_name>
```

More on this in the [Getting Started](https://bishwas-py.github.io/djapy/getting-started) docs section.
