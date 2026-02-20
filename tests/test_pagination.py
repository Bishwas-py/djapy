import json
import pytest

from tests.testapp.models import Item


@pytest.fixture
def many_items(db):
    return [Item.objects.create(title=f"Item {i}", price=i * 10) for i in range(25)]


class TestOffsetLimitPagination:
    def test_default_pagination(self, client, many_items):
        response = client.get("/items/paginated/offset/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data["items"]) == 10
        assert data["offset"] == 0
        assert data["limit"] == 10
        assert data["total"] == 25
        assert data["has_next"] is True
        assert data["has_previous"] is False
        assert data["total_pages"] == 3

    def test_second_page(self, client, many_items):
        response = client.get("/items/paginated/offset/?offset=10&limit=10")
        data = json.loads(response.content)
        assert len(data["items"]) == 10
        assert data["has_next"] is True
        assert data["has_previous"] is True
        assert data["current_page"] == 2

    def test_last_page(self, client, many_items):
        response = client.get("/items/paginated/offset/?offset=20&limit=10")
        data = json.loads(response.content)
        assert len(data["items"]) == 5
        assert data["has_next"] is False
        assert data["has_previous"] is True

    def test_custom_limit(self, client, many_items):
        response = client.get("/items/paginated/offset/?offset=0&limit=5")
        data = json.loads(response.content)
        assert len(data["items"]) == 5
        assert data["total_pages"] == 5

    def test_empty_results(self, client, db):
        response = client.get("/items/paginated/offset/")
        data = json.loads(response.content)
        assert len(data["items"]) == 0
        assert data["total"] == 0
        assert data["total_pages"] == 0

    def test_computed_fields(self, client, many_items):
        response = client.get("/items/paginated/offset/?offset=5&limit=10")
        data = json.loads(response.content)
        assert data["start_index"] == 6
        assert data["end_index"] == 15
        assert data["items_count"] == 10


class TestPageNumberPagination:
    def test_first_page(self, client, many_items):
        response = client.get("/items/paginated/page/")
        data = json.loads(response.content)
        assert response.status_code == 200
        assert len(data["items"]) == 10
        assert data["current_page"] == 1
        assert data["has_next"] is True
        assert data["has_previous"] is False
        assert data["is_first_page"] is True

    def test_second_page(self, client, many_items):
        response = client.get("/items/paginated/page/?page_number=2&page_size=10")
        data = json.loads(response.content)
        assert data["current_page"] == 2
        assert data["has_previous"] is True

    def test_last_page(self, client, many_items):
        response = client.get("/items/paginated/page/?page_number=3&page_size=10")
        data = json.loads(response.content)
        assert data["is_last_page"] is True
        assert data["has_next"] is False
        assert len(data["items"]) == 5

    def test_beyond_last_page(self, client, many_items):
        response = client.get("/items/paginated/page/?page_number=100&page_size=10")
        data = json.loads(response.content)
        assert len(data["items"]) == 0
        assert data["has_next"] is False

    def test_empty_queryset(self, client, db):
        response = client.get("/items/paginated/page/")
        data = json.loads(response.content)
        assert data["total"] == 0
        # Django's Paginator returns num_pages=1 for empty queryset
        # (allow_empty_first_page=True by default)
        assert data["num_pages"] == 1


class TestCursorPagination:
    def test_first_page_no_cursor(self, client, many_items):
        response = client.get("/items/paginated/cursor/?limit=5")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data["items"]) == 5
        assert data["has_next"] is True
        assert data["limit"] == 5

    def test_cursor_forward(self, client, many_items):
        resp1 = client.get("/items/paginated/cursor/?limit=5&ordering=asc")
        data1 = json.loads(resp1.content)
        cursor = data1["cursor"]
        assert cursor is not None

        resp2 = client.get(f"/items/paginated/cursor/?cursor={cursor}&limit=5&ordering=asc")
        data2 = json.loads(resp2.content)
        assert len(data2["items"]) == 5
        # Items should be different (next page)
        item_ids_1 = [i["id"] for i in data1["items"]]
        item_ids_2 = [i["id"] for i in data2["items"]]
        assert set(item_ids_1).isdisjoint(set(item_ids_2))

    def test_desc_ordering(self, client, many_items):
        response = client.get("/items/paginated/cursor/?limit=5&ordering=desc")
        data = json.loads(response.content)
        assert data["ordering"] == "desc"
        assert len(data["items"]) == 5

    def test_empty_queryset(self, client, db):
        response = client.get("/items/paginated/cursor/?limit=5")
        data = json.loads(response.content)
        assert len(data["items"]) == 0
        assert data["has_next"] is False
