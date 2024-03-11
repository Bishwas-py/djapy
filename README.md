# Introduction

This is the documentation for the `Djapy` library, which is designed to let you make RESTful APIs
within Django with as no boilerplate, using plain Python and Django, with the supremacy of Pydantic.

Djapy is molded according to `Django`'s philosophy of "batteries included", and is designed to
be as simple as possible to use, while still being powerful enough to handle most use cases.

```python
@djapify
def get_user(request) -> {200: UserSchema, 404: str}:
    return request.user
```

> It's that simple!

## Installation

Djapy is available on PyPI, and can be installed with `pip`:

```bash
pip install djapy
# or pip install git+https://github.com/Bishwas-py/djapy.git@main
```

## Creating a new project

To create a new project, run the following command:

```bash
django-admin startproject <project_name>
```

More on this in the [Usage](https://bishwas-py.github.io/djapy/usage/) section.