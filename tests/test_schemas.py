import pytest
from pydantic import ValidationError

from djapy.schema.schema import Schema, Form, QueryMapperSchema, Outsource, get_json_dict


class TestSchema:
    def test_is_empty_true(self):
        EmptySchema = type("EmptySchema", (Schema,), {"__annotations__": {}})
        assert EmptySchema.is_empty() is True

    def test_is_empty_false(self):
        class NonEmpty(Schema):
            name: str
        assert NonEmpty.is_empty() is False

    def test_from_attributes(self):
        class ItemSchema(Schema):
            name: str
            value: int

        class FakeObj:
            name = "test"
            value = 42

        result = ItemSchema.model_validate(FakeObj())
        assert result.name == "test"
        assert result.value == 42

    def test_validate_via_request(self):
        class SimpleSchema(Schema):
            name: str

        result = SimpleSchema.validate_via_request({"name": "hello"})
        assert result.name == "hello"

    def test_validate_via_request_invalid(self):
        class SimpleSchema(Schema):
            name: str

        with pytest.raises(ValidationError):
            SimpleSchema.validate_via_request({"wrong_key": "hello"})

    def test_model_dump_fast(self):
        class S(Schema):
            x: int
        obj = S(x=1)
        assert obj.model_dump_fast() == {"x": 1}

    def test_single_field_schema(self):
        class Inner(Schema):
            val: int

        class Wrapper(Schema):
            inner: Inner

        result = Wrapper._single()
        assert result is not None
        assert result[0] == "inner"


class TestForm:
    def test_cvar_c_type(self):
        assert Form.cvar_c_type == "application/x-www-form-urlencoded"

    def test_querydict_list_to_single(self):
        class MyForm(Form):
            name: str
            age: int

        result = MyForm.model_validate({"name": ["John"], "age": ["25"]})
        assert result.name == "John"
        assert result.age == 25


class TestQueryMapperSchema:
    def test_querydict_list_conversion(self):
        class QS(QueryMapperSchema):
            search: str

        result = QS.model_validate({"search": ["hello"]})
        assert result.search == "hello"

    def test_cvar_type(self):
        assert QueryMapperSchema.cvar_c_type == "_query_mapper"


class TestGetJsonDict:
    def test_parses_json_string(self):
        result = get_json_dict('{"key": "value"}')
        assert result == {"key": "value"}

    def test_nested_json(self):
        result = get_json_dict('{"outer": {"inner": 1}}')
        assert result == {"outer": {"inner": 1}}


class TestOutsource:
    def test_outsource_stores_original_object(self):
        class OS(Outsource):
            name: str

        # Outsource inherits from BaseModel, so we use dict input
        result = OS.model_validate({"name": "test"})
        assert result._obj is not None
        assert result.name == "test"
