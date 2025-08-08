> No Boilerplate, just rapid Django API ⚡️

Write powerful Django APIs with minimal code. Djapy combines Django's robustness with modern API development practices,
giving you a clean, intuitive way to build REST APIs.

[![PyPI version](https://badge.fury.io/py/djapy.svg)](https://badge.fury.io/py/djapy)
[![Python Versions](https://img.shields.io/pypi/pyversions/djapy.svg)](https://pypi.org/project/djapy)
[![Django Versions](https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2-blue)](https://github.com/Bishwas-py/djapy)
[![Downloads](https://static.pepy.tech/badge/djapy)](https://pepy.tech/project/djapy)

```python
@djapify
def get_user(request, username: str) -> UserSchema:
   return User.objects.get(username=username)
```

That's it. No serializers, no viewsets, no boilerplate - just pure Python.

## ✨ Why Djapy?

Write Django REST APIs that are simple by default, powerful when needed. Djapy works seamlessly with Django's ecosystem
while adding modern API features.

```python
# Works perfectly with Django decorators
@cache_page(BASIC_CACHE_1_HOUR)
@djapify
def get_posts(request, search: Optional[str] = None) -> List[PostSchema]:
   posts = Post.objects.all()
   if search:
      posts = posts.filter(title__icontains=search)
   return posts


# Need async? Just use async_djapify
@async_djapify
@paginate
async def get_comments(request, post_id: int) -> List[CommentSchema]:
   return await Comment.objects.filter(post_id=post_id).aall()
```

## 🚀 Key Features

- **Zero Boilerplate**: Build APIs with pure Python
- **Django Native**: Works seamlessly with Django's decorators and features
- **Type Safety**: Full Python type hints with Pydantic
- **Async When You Need It**: Optional async support for high-performance endpoints
- **Smart Authentication**: Simple session auth, customizable when needed
- **OpenAPI Support**: Automatic Swagger documentation
- **IDE Friendly**: Full intellisense support

## 🎯 Quick Start

1. **Install Djapy**

```bash
pip install djapy
```

2. **Create Your First API**

```python
from djapy import djapify, Schema


class PostSchema(Schema):
   title: str
   body: str
   author: str


@djapify
def create_post(request, data: PostSchema) -> {201: PostSchema}:
   post = Post.objects.create(**data.dict())
   return 201, post


# Want caching? Use Django's cache_page
@cache_page(3600)
@djapify
def get_post(request, post_id: int) -> PostSchema:
   return Post.objects.get(id=post_id)
```

## 🔥 Core Features

### 1. Simple by Default, Powerful When Needed

```python
# Simple endpoint
@djapify
def get_tag(request, tag_slug: str) -> TagSchema:
   return Tags.objects.get(slug=tag_slug)


# Need more power? Add async and pagination
@async_djapify
@paginate
async def get_tag_posts(request, tag_slug: str) -> List[PostSchema]:
   tag = await Tags.objects.aget(slug=tag_slug)
   return await tag.posts.aall()
```

### 2. Works with Django's Ecosystem

```python
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt


@cache_page(3600)
@csrf_exempt
@djapify(method="POST")
def create_user(request, data: UserSchema) -> {201: UserSchema}:
   user = User.objects.create(**data.dict())
   return 201, user
```

### 3. Simple Authentication

```python
@djapify(auth=SessionAuth)
def get_profile(request) -> ProfileSchema:
   return request.user.profile


# Need custom auth messages?
@djapify(auth=SessionAuth, msg={
   "message": "Please log in first",
   "redirect": "/login"
})
def protected_view(request) -> ProtectedSchema:
   return {"data": "secret"}
```

### 4. Type-Safe Responses

```python
@djapify
def get_post(request, post_id: int) -> {
   200: PostSchema,
   404: MessageSchema
}:
   try:
      return Post.objects.get(id=post_id)
   except Post.DoesNotExist:
      return 404, {
         "message": "Post not found",
         "type": "error"
      }
```

## 🔄 Migration from DRF

| DRF Concept | Djapy Equivalent                      |
|-------------|---------------------------------------|
| ViewSets    | Simple function views with `@djapify` |
| Serializers | Pydantic Schema models                |
| Permissions | Built-in auth system                  |
| Filters     | Native Python parameters              |
| Pagination  | `@paginate` decorator                 |

## 📚 Documentation

Visit [djapy-docs.pages.dev/](https://djapy-docs.pages.dev/) for comprehensive documentation.

## 🤝 Community & Support

- 📖 [Documentation](https://djapy.io)
- 💬 [Community](https://webmatrices.com/tags/django)
- 🐛 [Issue Tracker](https://github.com/Bishwas-py/djapy/issues)
- 📦 [PyPI](https://pypi.org/project/djapy)