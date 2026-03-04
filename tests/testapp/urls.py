from django.urls import path
from . import views

urlpatterns = [
    path("items/", views.list_items, name="list-items"),
    path("items/create/", views.create_item, name="create-item"),
    path("items/<int:pk>/", views.get_item, name="get-item"),
    path("items/search/", views.search_items, name="search-items"),
    path("items/protected/", views.protected_view, name="protected"),
    path("items/permission/", views.permission_view, name="permission"),
    path("items/public/", views.no_auth_view, name="public"),
    path("items/async/", views.async_list_items, name="async-list"),
    path("items/paginated/offset/", views.paginated_items_offset, name="paginated-offset"),
    path("items/paginated/page/", views.paginated_items_page, name="paginated-page"),
    path("items/paginated/cursor/", views.paginated_items_cursor, name="paginated-cursor"),
    path("items/form-create/", views.form_create_item, name="form-create"),
    path("items/multi-method/", views.multi_method_view, name="multi-method"),
    path("items/json-response/", views.json_response_view, name="json-response"),
    path("items/status-code/", views.status_code_view, name="status-code"),
]
