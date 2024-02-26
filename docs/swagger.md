# Swagger, swagger there you are

Well, djapy, one of the finest piece of software I've ever written, has a swagger documentation.
It is flawless, it is perfect, it is beautiful.

Here's how it looks like:

![Djapy Swagger Support](swagger_screenshot.png)

And here's how you can use it:

```python
from django.urls import path
from djapy import openapi

openapi.set_basic_info(
    title="Todo API",
    description="A simple todo API",
    version="0.0.1"
)

urlpatterns = [
    ...
    path('', openapi.urls),
]
```

And that's it. You can now access your swagger documentation at the url you've set in your `urls.py` file.

## Tags and descriptions

You can add tags and descriptions to your endpoints by using the `openapi_info` variable.

```python
openapi_info = {
    "tags": ["User"],
    "tags_info": [
        {
            "name": "User",
            "description": "User related endpoints",
            "externalDocs": {
                "description": "Find more info here",
                "url": "https://example.com"
            }
        }
    ]
}
```


Also, you can assign tags name using `@djapigy` decorator.

```python
from djapy import djapify


@djapify(openapi_tags=["todos"])
def todo_list(request):
    ...
```

> Suggestion: You can `openapi_info > tags_info` to add more information about the tags and `@djapify` to add tags to the endpoint.
Explain the tags in the `openapi_info` and use them accordingly with `@djapify` decorator.

It's that simple.
