# Pagination

You want something, djapily paginated? Right place you're in.

We provide three pagination out of the box; `OffsetLimitPagination`, `PageNumberPagination` and `CursorPagination`.

## OffsetLimitPagination

This is the default pagination mechanism in Djapy. It's simple and easy to use. It's based on the `offset` and `limit`
query parameters. Here's how you can use it:

```python
from djapy.pagination import OffsetLimitPagination, paginate


@djapify  # required
@paginate(OffsetLimitPagination)  # required, OR just @paginate, params: offset=0, limit=10
def todo_list(request) -> List[Todo]:
    return Todo.objects.all()
```

Make sure to add `paginate` decorator to your view and pass the pagination class as an argument. `List[Todo]` is the
return type hint of the view, also for Swagger documentation.

## PageNumberPagination

This is another pagination mechanism in Djapy. It's based on the `page` and `page_size` query parameters. Here's how you
can use it:

```python
from djapy.pagination import PageNumberPagination, paginate


@djapify  # required
@paginate(PageNumberPagination)  # required, OR just @paginate, params: page_number=1, page_size=10
def todo_list(request) -> List[Todo]:
    return Todo.objects.all()
```

## CursorPagination

This is the last pagination mechanism in Djapy. It's based on the `cursor` query parameter. Here's how you can use it:

```python
from djapy.pagination import CursorPagination, paginate


@djapify  # required
@paginate(CursorPagination)  # required, OR just @paginate, params: cursor=0, limit=10
def todo_list(request) -> List[Todo]:
    return Todo.objects.all()
```

> `cursor` is the primary key of the last object in the previous page.

## Extending Base Pagination

You can extend the base pagination mechanism to create your own custom pagination mechanism.

Here's an example of how you can do that:

```python
from djapy.pagination import BasePagination


class CursorPagination(BasePagination):  # example
    """Cursor-based pagination."""

    query = [
        ('cursor', conint(ge=0), 0),
        ('limit', conint(ge=0), 1),
        # ... your custom query parameters here
    ]

    class response(Schema, Generic[G_TYPE]):
        items: G_TYPE
        cursor: int | None
        limit: int
        has_next: bool
        # ... your custom fields here

        @model_validator(mode="before")
        def make_data(cls, queryset, info):
            if not isinstance(queryset, QuerySet):
                raise ValueError("The result should be a QuerySet")
            # ... your custom logic here

            return {
                "items": queryset_subset,
                "cursor": cursor,
                "limit": limit,
                "has_next": has_next,
            }
```