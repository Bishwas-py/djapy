# Middleware

Djapy provides a middleware for error handling. You can use it like this:

```python
MIDDLEWARE = [
    # rest of the middlewares
    'djapy.wrappers.mid.HandleErrorMiddleware'
]
```

## HandleErrorMiddleware

This middleware will handle all the errors and return a JSON response with the error message. The
logs will still be shown as usual, but the user will get a JSON response with the error message.
