import json
import pytest
from django.test import Client

from tests.testapp.models import Item


class TestValidationErrors:
    def test_missing_required_field(self, client, db):
        response = client.post(
            "/items/create/",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["type"] == "validation_error"
        assert data["error_count"] >= 1

    def test_wrong_type(self, client, db):
        response = client.post(
            "/items/create/",
            data=json.dumps({"title": "Test", "price": "not_a_number"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_constraint_violation(self, client, db):
        """Price must be > 0 per the schema Field(gt=0)."""
        response = client.post(
            "/items/create/",
            data=json.dumps({"title": "Test", "price": 0}),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestMethodNotAllowed:
    def test_get_on_post_only(self, client, db):
        response = client.get("/items/create/")
        assert response.status_code == 405
        data = json.loads(response.content)
        assert data["alias"] == "method_not_allowed"

    def test_delete_on_get_only(self, client, db):
        response = client.delete("/items/")
        assert response.status_code == 405
