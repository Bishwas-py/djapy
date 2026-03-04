import json
import pytest
from django.test import Client
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from djapy.core.auth.auth import BaseAuthMechanism, SessionAuth


class TestSessionAuthUnit:
    def test_unauthenticated_returns_403(self, rf):
        auth = SessionAuth()
        request = rf.get("/")
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
        result = auth.authenticate(request)
        assert result == (403, {"message": "Unauthorized"})

    def test_authenticated_returns_none(self, rf, user):
        auth = SessionAuth()
        request = rf.get("/")
        request.user = user
        result = auth.authenticate(request)
        assert result is None

    def test_schema_returns_security_schemes(self):
        auth = SessionAuth()
        schema = auth.schema()
        assert "SessionAuth" in schema
        assert "CSRFTokenAuth" in schema
        assert schema["SessionAuth"]["type"] == "apiKey"

    def test_app_schema(self):
        auth = SessionAuth()
        app_schema = auth.app_schema()
        assert "SessionAuth" in app_schema


class TestBaseAuthMechanism:
    def test_default_message(self):
        auth = BaseAuthMechanism()
        assert auth.message_response == {"message": "Unauthorized"}

    def test_custom_message(self):
        auth = BaseAuthMechanism(message_response={"message": "Go away"})
        assert auth.message_response == {"message": "Go away"}

    def test_set_message_response(self):
        auth = BaseAuthMechanism()
        auth.set_message_response({"message": "Custom"})
        assert auth.message_response == {"message": "Custom"}

    def test_authenticate_returns_none_by_default(self, rf):
        auth = BaseAuthMechanism()
        request = rf.get("/")
        assert auth.authenticate(request) is None


class TestAuthViews:
    def test_protected_view_unauthenticated(self, client, db):
        response = client.get("/items/protected/")
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data["message"] == "Unauthorized"

    def test_protected_view_authenticated(self, auth_client, db):
        response = auth_client.get("/items/protected/")
        assert response.status_code == 200

    def test_public_view_no_auth_needed(self, client, db):
        response = client.get("/items/public/")
        assert response.status_code == 200

    def test_permission_view_without_perm(self, auth_client, db):
        response = auth_client.get("/items/permission/")
        assert response.status_code == 403

    def test_permission_view_with_perm(self, user, db):
        perm = Permission.objects.get(
            codename="add_item",
            content_type__app_label="testapp",
        )
        user.user_permissions.add(perm)
        user.save()
        c = Client()
        c.login(username="testuser", password="testpass123")
        response = c.get("/items/permission/")
        assert response.status_code == 200
