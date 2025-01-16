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

## Features

- Complete input/output data flow control
- Extensible and extremely customizable auth; SessionAuth provided in-built
- Hyper type checking, pydantic-based, and swagger integrated
- CursorPagination, OffsetLimitPagination and PageNumber out of the box; with ability to create custom pagination
- Validation, validation messages, with complete control over each validation process
- Customizable error handling, and error messages
- Completely Django friendly, and can be used with any Django project

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

> See sample: [project](https://github.com/Bishwas-py/djapy-todo).
> Fork project: [bishwas-py/djapy](https://github.com/Bishwas-py/djapy).

More on this in the [Usage](https://djapy.io/usage/) section.

## Contribution Guidelines

We welcome all contributions to Djapy, and have a set of guidelines to ensure that the process is as smooth as possible.

Please read the [Contribution Guidelines](https://djapy.io/contribution/) before contributing.
