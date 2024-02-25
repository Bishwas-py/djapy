# Usage

Here's how you can use this package:

```python
@djapify
def get_user(request, data: UserCreationSchema) -> {200: UserSchema, 404: MessageOut}:
    if request.user.has_perm('users.can_create_user'):
        user = User.objects.create_user(username=data.username, email=data.email)
        return user
    else:
        return {
            'message': 'You are not allowed to create a user',
            'alias': 'not_allowed'
        }
    return request.user  # or 200, request.user
```

- `djapify` is a decorator that takes a function and returns a new function that can be used as a Django view.
- The function signature is `def get_user(request, data: UserCreationSchema) -> {200: UserSchema, 404: MessageOut}:`
    - The first argument is always the request object.
    - The rest of the arguments are the parameters that you want to accept from the request.
    - The return type is a dictionary that maps status codes to Schema[Pydantic models].
- The function body can be anything you want, as long as it returns a dictionary that maps status codes to Pydantic
  models.
  3

## Request

The schema is defined using Pydantic models. Here's an example:

```python
# schemas.py
from djapy import Schema


class CreateUserSchema(Schema):
    username: str
    email: EmailStr


# views.py
@djapify
def create_user(request, data: CreateUserSchema) -> {200: UserSchema, 400: str}:
    user = User.objects.create_user(username=data.username, password=data.password)
    return user
```

- `Schema` is a subclass of `pydantic.BaseModel` that adds some extra functionality.
- The schema is used to validate the request data before it's passed to the view function.
- If the data is invalid, a pydantic error will be raised and returned as a response.

#### Invalid request error response

```json
{
  "error": [
    {
      "type": "missing",
      "loc": [
        "username"
      ],
      "msg": "Field required",
      "input": {
        "my_id": "1",
        "id": "1"
      },
      "url": "https://errors.pydantic.dev/2.6/v/missing"
    },
    {
      "type": "missing",
      "loc": [
        "email"
      ],
      "msg": "Field required",
      "input": {
        "my_id": "1",
        "id": "1"
      },
      "url": "https://errors.pydantic.dev/2.6/v/missing"
    }
  ],
  "error_count": 2,
  "title": "CreateUserSchema"
}
```

### Query Parameters

You can also accept query parameters in your view function:

```python
@djapify
def get_user(request, username: str) -> {200: UserSchema, 404: str}:
    user = User.objects.get(username=username)
    return user
```

#### Allowed query parameter types

- `str`
- `int`
- `float`
- `bool`
- `datetime`

> If anything else is passed, it will be accepted as a data parameter, not a query parameter.
> Like: list[str], dict[str, int], etc.

## Response

The response is automatically serialized to JSON using the Pydantic model.

```python
# schemas.py
from djapy import Schema


class UserSchema(Schema):
    username: str
    email: str


# views.py
@djapify
def get_user(request, username: str) -> {200: UserSchema, 404: str}:
    user = User.objects.get(username=username)
    return user


# urls.py
urlpatterns = [
    path('get-user/', views.get_user, name='get-user'),
]
```

- The response will be serialized to JSON using the `UserSchema` model, if not valid, pydantic error will be raised.
- If the response is a valid instance of the model, it will be serialized to JSON and returned with a 200 status code.
- If the response is a string, it will be returned with a 200 status code.

#### Invalid error response

```json
{
  "error": [
    {
      "type": "missing",
      "loc": [
        "response",
        "message"
      ],
      "msg": "Field required",
      "input": {
        "error": "You are not allowed to create a user"
      },
      "url": "https://errors.pydantic.dev/2.6/v/missing"
    }
  ],
  "error_count": 1,
  "title": "output"
}
```

## Custom error response

You can also return a custom error response, by create error handlers inside `djapy_ext/errorhandler.py`;

```python
from your_custom_exptions.exceptions import MessageOut


def handle_message_out(request, exception: MessageOut):
    print('Value: Handler executed: ', request)
    return {
        'message': exception.message,
        'alias': exception.alias,
        'message_type': exception.message_type,
    }
```

> Make sure your handler function name is `handle_<exception_name>`

And then, you can use it in your view function:

```python
@djapify
def get_user(request, username: str) -> {200: UserSchema, 404: MessageOut}:
    user = User.objects.get(username=username)
    if user:
        return user
    else:
        raise MessageOut('User not found', 'user_not_found', 'error')
```

- If exception is raised, the handler will be executed and the response will be returned.


