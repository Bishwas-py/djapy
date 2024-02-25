# Introduction

This is the documentation for the `Djapy` library, which is designed to let you make RESTful APIs
within Django with as no boilerplate, using plain Python and Django, with the supremacy of Pydantic.

Djapy is molded according to `Django`'s philosophy of "batteries included", and is designed to
be as simple as possible to use, while still being powerful enough to handle most use cases.

> We believe in "Do not use a Framework inside an awesome Framework".

```python
@djapify
@djapy_login_required
def get_user(request) -> {200: UserSchema, 400: ErrorMessage}:
    return request.user
```

It does not enforce any particular design pattern, and is designed to be as flexible as possible,
while still being easy to use.

## Installation

Djapy is available on PyPI, and can be installed with `pip`:

```bash
pip install djapy
```

## Creating a new project

To create a new project, run the following command:

```bash
django-admin startproject <project_name>
```

More on this in the [Getting Started](getting-started.md) section.