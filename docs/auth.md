# Authentication

Djapy is very welcoming toward new and better authentication systems. It provides a very simple and easy to use 
authentication system. Djapy is a Django's friendly package, so it's authentication system is also Django's friendly.

For general authentication, we using session based authentication. But, we also provide token based authentication 
(available) and will be providing JWT based authentication (in future).

## Authentication Decorators

```python
from djapy.auth.dec import djapy_login_required
```

We have one decorator for Django's session based authentication, `@djapy_login_required`.


```python
@djapy_login_required
@input_required(['title'])
def todo_post(request, data, *args, **kwargs):
    will_be_completed_at = request.POST.get('will_be_completed_at')
    todo = Todo.objects.create(
        title=data.title,
        will_be_completed_at=will_be_completed_at,
        user_id=request.user.id
    )
    return todo
```

Here, `@djapy_login_required` will check if the user is logged in or not via `request.user.is_authenticated`. If the
user is not logged in, it will return a JSON error message to the client.

```python
@csrf_exempt
@node_to_json_response
@input_required(['username', 'password'])
def login_for_session(request, data, *args, **kwargs):
    user = authenticate(username=data.username, password=data.password)
    if user:
        login(request, user)
    return JsonResponse({
        'session_key': request.session.session_key,
        'is_authenticated': user.is_authenticated if user else False,
        'expiry_age': request.session.get_expiry_age(),
        'csrf_token': request.COOKIES.get('csrftoken'),
        'id': user.id if user else None,
    })
```

The above code is a simple login view for session based authentication. It will return a JSON response with the
session key, CSRF token, expiry age, and the user's id. You can store the session key and CSRF token in the client's
side and send them with every request in the header.


