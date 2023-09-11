# For contributors

This is a guide for contributors to the project. If you are looking for the development contribution,
wanna know what's going on, or why use any decorator or class, this is the place to be.

## Internal structure

```text
djapy
├── data
│   ├── dec.py
│   ├── fields.py
│   ├── __init__.py
│   └── mapper.py
├── decs
│   ├── auth.py
│   ├── __init__.py
│   └── wrappers.py
├── __init__.py
├── mixins
│   ├── __init__.py
│   └── permissions.py
├── pagination
│   ├── dec.py
│   ├── __init__.py
│   └── paginator.py
├── parser
│   ├── __init__.py
│   └── models_parser.py
├── utils
│   ├── defaults.py
│   ├── __init__.py
│   ├── mapper.py
│   ├── response_format.py
│   └── types.py
└── views
    ├── generics.py
    └── __init__.py
```

Each folder has a specific purpose, and each file has a specific purpose too, including the `__init__.py` files.

Check the [data](data.md) directory documentation.