import pytest
from django.test import RequestFactory

from djapy.openapi import openapi


class TestOpenAPIGeneration:
    def setup_method(self):
        self.rf = RequestFactory()
        # Reset openapi state between tests
        openapi.paths = {}
        openapi.components = {"schemas": {}}
        openapi.definitions = {}
        openapi.tags = []

    def test_generates_schema(self):
        request = self.rf.get("/")
        schema = openapi.dict(request, use_cache=False)
        assert schema["openapi"] == "3.1.0"
        assert "paths" in schema
        assert "components" in schema
        assert "info" in schema

    def test_discovers_djapy_views(self):
        request = self.rf.get("/")
        schema = openapi.dict(request, use_cache=False)
        assert len(schema["paths"]) > 0

    def test_paths_have_methods(self):
        request = self.rf.get("/")
        schema = openapi.dict(request, use_cache=False)
        for path_key, path_obj in schema["paths"].items():
            methods = {"get", "post", "put", "patch", "delete", "options", "head"}
            assert any(m in path_obj for m in methods), f"No method found in {path_key}"

    def test_set_basic_info(self):
        openapi.set_basic_info(
            title="Test API",
            description="A test API",
            version="2.0.0",
        )
        assert openapi.info.title == "Test API"
        assert openapi.info.version == "2.0.0"

    def test_servers_include_request_url(self):
        request = self.rf.get("/")
        schema = openapi.dict(request, use_cache=False)
        assert len(schema["servers"]) >= 1
        assert "url" in schema["servers"][0]

    def test_is_djapy_openapi_true(self):
        class FakeView:
            djapy = True
            openapi = True
        assert openapi.is_djapy_openapi(FakeView) is True

    def test_is_djapy_openapi_false(self):
        class FakeView:
            djapy = False
        assert openapi.is_djapy_openapi(FakeView) is False
