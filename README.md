> No Boilerplate, just rapid Django API ⚡️

Write powerful Django APIs with minimal code. Djapy combines Django's robustness with modern API development practices,
giving you a clean, intuitive way to build REST APIs.

[![PyPI version](https://badge.fury.io/py/djapy.svg)](https://badge.fury.io/py/djapy)
[![Python Versions](https://img.shields.io/pypi/pyversions/djapy.svg)](https://pypi.org/project/djapy/)
[![Django Versions](https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2-blue)](https://github.com/Bishwas-py/djapy)
[![Downloads](https://static.pepy.tech/badge/djapy)](https://pepy.tech/project/djapy)

```python
@djapify
def get_user(request, user_id: int) -> UserSchema:
   return User.objects.get(id=user_id)
```

## ✨ Why Djapy?

```python
from djapy import djapify, Schema


class UserOut(BaseModel):
   id: int
   username: str
   is_active: bool


@djapify
def get_users(request) -> list[UserOut]:
   return User.objects.filter(is_active=True)
```

Write Django REST APIs in pure Python. No serializers, no viewsets, no boilerplate,
no external url routers - just clean, typed, and maintainable code.

## 🚀 Key Features

- **Zero Boilerplate**: Build APIs with pure Python and Django
- **Type Safety**: Full Python type hints support
- **Modern Validation**: Built-in Pydantic integration
- **Hyperfast Performance**: Optimized for speed
- **Django Compatible**: Works with any Django project
- **OpenAPI Support**: Automatic Swagger documentation
- **IDE Friendly**: Full intellisense, endpoints (PyCharm) and type support

## 🎯 Quick Start

1. **Install Djapy**

```bash
pip install djapy
```

2. **Create Your First API**

```python
from djapy import djapify, Schema
from django.contrib.auth.models import User


class UserSchema(Schema):
   id: int
   username: str
   email: str


@djapify
def list_users(request) -> list[UserSchema]:
   return User.objects.all()


@djapify
def get_user(request, user_id: int) -> {200: UserSchema, 404: str}:
   try:
      return User.objects.get(id=user_id)
   except User.DoesNotExist:
      return "User not found", 404
```

3. **Add to URLs**

```python
from django.urls import path

urlpatterns = [
   path('users/', list_users),
   path('users/<int:user_id>/', get_user),
]
```

## 🔥 Core Features

### 1. Native Type System

```python
from typing import Optional
from djapy import djapify, Schema
from djapy.pagination import paginate


class UserFilter(Schema):
   search: Optional[str]
   is_active: bool = True


@djapify
@paginate
def search_users(request, filters: UserFilter) -> list[Schema]:
   queryset = User.objects.filter(is_active=filters.is_active)
   if filters.search:
      queryset = queryset.filter(username__icontains=filters.search)
   return queryset
```

### 2. Smart Request Handling

```python
@djapify
def create_user(request, data: UserCreate, team_id: int) -> {201: UserSchema}:
   # Automatic validation and parsing
   return 201, User.objects.create(**data.dict())
```

Learn more about type system and requests, [here](https://djapy.io/usage/request/).

### 3. Error Handling

```python
@djapify
def make_payment(request, amount: float) -> {200: PaymentSchema}:
   if request.user.balance < amount:
      raise MessageException("Insufficient balance")
   return Payment.objects.create(user=request.user, amount=amount)
```

More about error handling, [here](https://djapy.io/usage/error-handling/).

## 🔄 Migration from DRF

| DRF Concept | Djapy Equivalent                     |
|-------------|--------------------------------------|
| ViewSets    | Function-based views with `@djapify` |
| Serializers | Pydantic models                      |
| Permissions | Python decorators                    |
| Filters     | Query parameters                     |
| Pagination  | Built-in pagination helpers          |

## 📚 Documentation

Visit [djapy.io](https://djapy.io) for comprehensive documentation.

## 🤝 Community & Support

- 📖 [Documentation](https://djapy.io)
- 💬 [Community](https://webmatrices.com/tag/django)
- 🐛 [Issue Tracker](https://github.com/Bishwas-py/djapy/issues)
- 📦 [PyPI](https://pypi.org/project/djapy)
