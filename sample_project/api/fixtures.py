"""
Test fixtures and utilities for API testing
"""
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async


class TestDataMixin:
    """Mixin to provide common test data"""
    
    @classmethod
    def create_test_user(cls, username="testuser", email="test@example.com"):
        """Create a test user synchronously"""
        return User.objects.create_user(
            username=username,
            email=email,
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
    
    @classmethod
    async def acreate_test_user(cls, username="testuser", email="test@example.com"):
        """Create a test user asynchronously"""
        return await User.objects.acreate(
            username=username,
            email=email,
            first_name="Test",
            last_name="User",
            password="testpass123"
        )


# Sample test data
SAMPLE_USER_DATA = {
    "valid_user": {
        "username": "newuser",
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User"
    },
    "invalid_user_short_username": {
        "username": "ab",
        "email": "invalid@example.com",
        "first_name": "Invalid",
        "last_name": "User"
    },
    "invalid_user_no_email": {
        "username": "noemailu",
        "first_name": "No",
        "last_name": "Email"
    }
}

SAMPLE_POST_DATA = {
    "valid_post": {
        "title": "Test Post Title",
        "content": "This is a comprehensive test post content that should pass validation.",
        "author_id": 1
    },
    "invalid_post_empty_title": {
        "title": "",
        "content": "Content without title",
        "author_id": 1
    },
    "invalid_post_no_author": {
        "title": "Post without author",
        "content": "This post has no valid author",
        "author_id": 99999
    }
}

MESSAGE_ERROR_TEST_CASES = [
    {
        "error_type": "validation",
        "expected_message": "Validation failed: Invalid input data",
        "expected_alias": "validation_error",
        "expected_type": "error"
    },
    {
        "error_type": "permission",
        "expected_message": "Permission denied: You don't have access to this resource",
        "expected_alias": "permission_error",
        "expected_type": "error"
    },
    {
        "error_type": "success",
        "expected_message": "Operation completed successfully!",
        "expected_alias": "success_message",
        "expected_type": "success"
    },
    {
        "error_type": "warning",
        "expected_message": "This is a warning message",
        "expected_alias": "warning_message",
        "expected_type": "warning"
    },
    {
        "error_type": "info",
        "expected_message": "This is an informational message",
        "expected_alias": "info_message",
        "expected_type": "info"
    }
]
