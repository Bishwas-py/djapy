import inspect
from typing import Annotated, Union, List, Optional

from pydantic import BaseModel, Field

from djapy.core.type_check import (
    is_param_query_type,
    is_base_query_type,
    is_union_of_basic_types,
    is_annotated_of_basic_types,
    schema_type,
    is_django_type,
    is_data_type,
    get_type_name,
    basic_query_schema,
)


class SampleSchema(BaseModel):
    name: str


def _make_param(name: str, annotation, default=inspect.Parameter.empty):
    return inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=annotation, default=default)


class TestIsBaseQueryType:
    def test_str(self):
        assert is_base_query_type(str) is True

    def test_int(self):
        assert is_base_query_type(int) is True

    def test_float(self):
        assert is_base_query_type(float) is True

    def test_bool(self):
        assert is_base_query_type(bool) is True

    def test_pydantic_model_not_query(self):
        assert is_base_query_type(SampleSchema) is False

    def test_list_is_query(self):
        assert is_base_query_type(list) is True

    def test_dict_not_query(self):
        assert is_base_query_type(dict) is False


class TestIsUnionOfBasicTypes:
    def test_str_or_int(self):
        assert is_union_of_basic_types(str | int) is True

    def test_str_or_float_or_bool(self):
        assert is_union_of_basic_types(str | float | bool) is True

    def test_str_or_dict_not_basic(self):
        assert is_union_of_basic_types(str | dict) is False

    def test_plain_str_not_union(self):
        assert is_union_of_basic_types(str) is False


class TestIsAnnotatedOfBasicTypes:
    def test_annotated_str_with_field(self):
        ann = Annotated[str, Field(description="test")]
        assert is_annotated_of_basic_types(ann) is True

    def test_annotated_int(self):
        ann = Annotated[int, Field(ge=0)]
        assert is_annotated_of_basic_types(ann) is True

    def test_annotated_model_not_basic(self):
        ann = Annotated[SampleSchema, Field()]
        assert is_annotated_of_basic_types(ann) is False

    def test_plain_str_not_annotated(self):
        assert is_annotated_of_basic_types(str) is False


class TestIsParamQueryType:
    def test_str_param(self):
        param = _make_param("q", str)
        assert is_param_query_type(param) is True

    def test_int_param(self):
        param = _make_param("pk", int)
        assert is_param_query_type(param) is True

    def test_schema_param_not_query(self):
        param = _make_param("data", SampleSchema)
        assert is_param_query_type(param) is False

    def test_annotated_str_param(self):
        param = _make_param("q", Annotated[str, Field()])
        assert is_param_query_type(param) is True


class TestSchemaType:
    def test_pydantic_model(self):
        assert schema_type(SampleSchema) == SampleSchema

    def test_str_not_schema(self):
        assert schema_type(str) is None

    def test_param_with_model(self):
        param = _make_param("data", SampleSchema)
        assert schema_type(param) == SampleSchema

    def test_param_with_str(self):
        param = _make_param("q", str)
        assert schema_type(param) is None


class TestGetTypeName:
    def test_str(self):
        assert get_type_name(str) == "str"

    def test_int(self):
        assert get_type_name(int) == "int"

    def test_bool(self):
        assert get_type_name(bool) == "bool"


class TestBasicQuerySchema:
    def test_str_param(self):
        param = _make_param("q", str)
        result = basic_query_schema(param)
        assert result == {"type": "string"}

    def test_int_param(self):
        param = _make_param("pk", int)
        result = basic_query_schema(param)
        assert result == {"type": "integer"}

    def test_string_slug(self):
        result = basic_query_schema("slug")
        assert result == {"type": "string"}
