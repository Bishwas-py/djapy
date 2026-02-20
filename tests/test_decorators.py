import json
import pytest
from django.test import Client

from tests.testapp.models import Item


@pytest.fixture
def items(db):
    return [
        Item.objects.create(title="Item A", price=10.00),
        Item.objects.create(title="Item B", price=20.00),
        Item.objects.create(title="Item C", price=30.00, is_active=False),
    ]


class TestDjapifySync:
    def test_list_items_returns_200(self, client, items):
        response = client.get("/items/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 3

    def test_list_items_json_content_type(self, client, items):
        response = client.get("/items/")
        assert "application/json" in response["Content-Type"]

    def test_create_item_with_json_body(self, client, db):
        response = client.post(
            "/items/create/",
            data=json.dumps({"title": "New Item", "price": 15.50}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["title"] == "New Item"
        assert Item.objects.filter(title="New Item").exists()

    def test_create_item_validation_error(self, client, db):
        response = client.post(
            "/items/create/",
            data=json.dumps({"title": "Bad", "price": -5}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_item_by_pk(self, client, items):
        item = items[0]
        response = client.get(f"/items/{item.pk}/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["title"] == "Item A"
        assert data["id"] == item.pk

    def test_get_item_not_found(self, client, db):
        response = client.get("/items/99999/")
        assert response.status_code == 404
        data = json.loads(response.content)
        assert data["alias"] == "not_found"

    def test_query_params(self, client, items):
        response = client.get("/items/search/?q=Item A&active=true")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]["title"] == "Item A"

    def test_query_params_filter_inactive(self, client, items):
        response = client.get("/items/search/?q=Item C&active=false")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 1


class TestMethodRestriction:
    def test_post_only_rejects_get(self, client, db):
        response = client.get("/items/create/")
        assert response.status_code == 405

    def test_multi_method_allows_get(self, client, items):
        response = client.get("/items/multi-method/")
        assert response.status_code == 200

    def test_multi_method_allows_post(self, client, items):
        response = client.post("/items/multi-method/", content_type="application/json")
        assert response.status_code == 200

    def test_multi_method_rejects_put(self, client, items):
        response = client.put("/items/multi-method/", content_type="application/json")
        assert response.status_code == 405


class TestJsonResponsePassthrough:
    def test_returns_custom_json(self, client, db):
        response = client.get("/items/json-response/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data == {"custom": "response"}


class TestStatusCodes:
    def test_returns_200(self, client, items):
        response = client.post(
            "/items/status-code/?fail=false",
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_returns_400(self, client, items):
        response = client.post(
            "/items/status-code/?fail=true",
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["alias"] == "bad_request"


class TestAsyncDjapify:
    def test_async_list_items(self, client, items):
        response = client.get("/items/async/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert isinstance(data, list)

    def test_async_rejects_non_coroutine(self):
        from djapy import async_djapify
        with pytest.raises(ValueError, match="must be async"):
            @async_djapify
            def not_async(request):
                pass
