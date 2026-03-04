import pytest
from django.contrib.auth.models import User
from django.test import Client, RequestFactory


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", password="adminpass123", email="admin@test.com"
    )


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def auth_client(user):
    c = Client()
    c.login(username="testuser", password="testpass123")
    return c


@pytest.fixture
def admin_client(admin_user):
    c = Client()
    c.login(username="admin", password="adminpass123")
    return c


@pytest.fixture
def rf():
    return RequestFactory()
