from django.http import HttpRequest, JsonResponse
from djapy import djapify, async_djapify
from djapy.core.auth import djapy_auth, SessionAuth
from djapy.pagination import OffsetLimitPagination, PageNumberPagination, CursorPagination
from djapy.pagination.dec import paginate

from .models import Item
from .schemas import (
    ItemSchema, ItemDetailSchema, ItemCreateSchema,
    ItemFormSchema, ErrorSchema,
)


@djapify
def list_items(request: HttpRequest) -> {200: list[ItemSchema]}:
    return 200, Item.objects.all()


@djapify(method="POST")
def create_item(request: HttpRequest, data: ItemCreateSchema) -> {200: ItemSchema, 400: ErrorSchema}:
    item = Item.objects.create(**data.model_dump())
    return 200, item


@djapify
def get_item(request: HttpRequest, pk: int) -> {200: ItemDetailSchema, 404: ErrorSchema}:
    try:
        item = Item.objects.get(pk=pk)
    except Item.DoesNotExist:
        return 404, {"message": "Item not found", "alias": "not_found"}
    return 200, item


@djapify(method="GET")
def search_items(request: HttpRequest, q: str, active: bool = True) -> {200: list[ItemSchema]}:
    qs = Item.objects.filter(title__icontains=q, is_active=active)
    return 200, qs


@djapify
@djapy_auth(SessionAuth)
def protected_view(request: HttpRequest) -> {200: list[ItemSchema]}:
    return 200, Item.objects.all()


@djapify
@djapy_auth(SessionAuth, permissions=["testapp.add_item"])
def permission_view(request: HttpRequest) -> {200: list[ItemSchema]}:
    return 200, Item.objects.all()


@djapify
def no_auth_view(request: HttpRequest) -> {200: list[ItemSchema]}:
    return 200, Item.objects.all()


@async_djapify
async def async_list_items(request: HttpRequest) -> {200: list[ItemSchema]}:
    from asgiref.sync import sync_to_async
    items = await sync_to_async(list)(Item.objects.all())
    return 200, items


@djapify
@paginate(OffsetLimitPagination)
def paginated_items_offset(request: HttpRequest) -> {200: list[ItemSchema]}:
    return 200, Item.objects.all()


@djapify
@paginate(PageNumberPagination)
def paginated_items_page(request: HttpRequest) -> {200: list[ItemSchema]}:
    return 200, Item.objects.all()


@djapify
@paginate(CursorPagination)
def paginated_items_cursor(request: HttpRequest) -> {200: list[ItemSchema]}:
    return 200, Item.objects.all()


@djapify(method="POST")
def form_create_item(request: HttpRequest, data: ItemFormSchema) -> {200: ItemSchema}:
    item = Item.objects.create(title=data.title, description=data.description)
    return 200, item


@djapify(method=["GET", "POST"])
def multi_method_view(request: HttpRequest) -> {200: list[ItemSchema]}:
    return 200, Item.objects.all()


@djapify
def json_response_view(request: HttpRequest) -> {200: ItemSchema}:
    return JsonResponse({"custom": "response"})


@djapify(method="POST")
def status_code_view(request: HttpRequest, fail: bool = False) -> {200: ItemSchema, 400: ErrorSchema}:
    if fail:
        return 400, {"message": "Intentional failure", "alias": "bad_request"}
    item = Item.objects.first()
    return 200, item
