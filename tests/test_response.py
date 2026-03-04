from pydantic import ValidationError, BaseModel

from djapy.core.response import (
    create_json_from_validation_error,
    create_validation_error,
    format_error_response,
)


class StubModel(BaseModel):
    name: str
    age: int


class TestCreateJsonFromValidationError:
    def test_detailed_format(self):
        try:
            StubModel(name=123, age="not_int")
        except ValidationError as e:
            result = create_json_from_validation_error(e, detailed=True)

        assert result["type"] == "validation_error"
        assert result["error_count"] >= 1
        assert "errors" in result
        assert "title" in result

    def test_simplified_format(self):
        try:
            StubModel(name=123, age="not_int")
        except ValidationError as e:
            result = create_json_from_validation_error(e, detailed=False)

        assert result["type"] == "validation_error"
        assert "errors" in result
        for err in result["errors"]:
            assert "field" in err
            assert "message" in err
            assert "type" in err


class TestCreateValidationError:
    def test_creates_validation_error(self):
        exc = create_validation_error("TestTitle", "field_name", "missing")
        assert isinstance(exc, ValidationError)
        assert exc.error_count() == 1

    def test_with_custom_message(self):
        exc = create_validation_error("TestTitle", "email", "missing", msg="Invalid email")
        assert isinstance(exc, ValidationError)
        errors = exc.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("email",)


class TestFormatErrorResponse:
    def test_basic_error(self):
        result = format_error_response("auth_error", "Not authenticated")
        assert result == {
            "type": "auth_error",
            "message": "Not authenticated",
            "status": 400,
        }

    def test_with_details(self):
        result = format_error_response(
            "validation_error", "Bad input", details={"field": "name"}, status_code=422
        )
        assert result["status"] == 422
        assert result["details"] == {"field": "name"}

    def test_without_details_no_key(self):
        result = format_error_response("error", "msg")
        assert "details" not in result
