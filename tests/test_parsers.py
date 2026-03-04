import json
import pytest

from tests.testapp.models import Item


@pytest.fixture
def items_fixture(db):
    return [
        Item.objects.create(title="Item X", price=10),
        Item.objects.create(title="Item Y", price=20),
    ]


class TestJsonBodyParsing:
    def test_parses_json_body(self, client, db):
        response = client.post(
            "/items/create/",
            data=json.dumps({"title": "From JSON", "price": 10}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["title"] == "From JSON"

    def test_empty_json_body(self, client, db):
        response = client.post(
            "/items/create/",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400


class TestFormDataParsing:
    def test_parses_form_data(self, client, db):
        response = client.post(
            "/items/form-create/",
            data={"title": "From Form", "description": "desc"},
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["title"] == "From Form"


class TestQueryParamParsing:
    def test_string_query_param(self, client, items_fixture):
        response = client.get("/items/search/?q=Item")
        assert response.status_code == 200

    def test_bool_query_param(self, client, items_fixture):
        response = client.get("/items/search/?q=X&active=false")
        assert response.status_code == 200

    def test_url_path_param(self, client, items_fixture):
        item = items_fixture[0]
        response = client.get(f"/items/{item.pk}/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["id"] == item.pk


class TestParserTupleAnnotation:
    def test_parse_dict_annotation(self):
        from djapy.core.parser import parse_tuple_annotation
        from djapy.schema.schema import Schema

        class S(Schema):
            x: int

        result = parse_tuple_annotation({200: S})
        assert result == {200: S}

    def test_parse_single_type(self):
        from djapy.core.parser import parse_tuple_annotation
        from djapy.schema.schema import Schema

        class S(Schema):
            x: int

        result = parse_tuple_annotation(S)
        assert result == {200: S}

    def test_prepare_schema_dict(self):
        from djapy.core.parser import prepare_schema

        result = prepare_schema({200: str, 404: str})
        assert result == {200: str, 404: str}

    def test_prepare_schema_single(self):
        from djapy.core.parser import prepare_schema

        result = prepare_schema(str)
        assert result == {200: str}
