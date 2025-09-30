from typing import List, Optional
from django.http import JsonResponse
from django.contrib.auth.models import User
from djapy import async_djapify, openapi
from djapy.pagination import paginate
from djapy.schema.schema import QueryList
from asgiref.sync import sync_to_async
from djapy_ext.exception import MsgErr
from datetime import datetime
from .schema import (
    UserCreateSchema,
    UserResponseSchema,
    PostCreateSchema,
    PostResponseSchema,
    HelloResponseSchema,
    ErrorResponseSchema,
)


# Configure OpenAPI info
openapi.set_basic_info(
    title="Sample Async Djapy API",
    description="A sample Django API built with async Djapy for testing and demonstration",
    version="1.0.0",
    tags_info=[
        {"name": "users", "description": "User management operations"},
        {"name": "posts", "description": "Post management operations"},
        {"name": "general", "description": "General API endpoints"},
    ]
)


@async_djapify(
    method='GET',
    tags=['general']
)
async def hello_world(request) -> HelloResponseSchema:
    """Simple async hello world endpoint to test basic djapy functionality."""
    from datetime import datetime
    
    return {
        "message": "Hello from Async Djapy!",
        "timestamp": datetime.now().isoformat(),
        "user": request.user.username if request.user.is_authenticated else None
    }


@async_djapify(
    method='GET',
    tags=['users']
)
@paginate
async def list_users(request, **kwargs) -> QueryList[UserResponseSchema]:
    """List all users with pagination support (async)."""
    users = await sync_to_async(User.objects.all)()
    return users


@async_djapify(
    method='GET',
    tags=['users']
)
async def get_user(request, user_id: int) -> {200: UserResponseSchema, 404: ErrorResponseSchema}:
    """Get a specific user by ID (async)."""
    try:
        user = await User.objects.aget(id=user_id)
        return user
    except User.DoesNotExist:
        return 404, {"error": "User not found", "detail": f"No user found with ID {user_id}"}


@async_djapify(
    method='POST',
    tags=['users']
)
async def create_user(request, data: UserCreateSchema) -> {201: UserResponseSchema, 400: ErrorResponseSchema}:
    """Create a new user (async)."""
    # Check if username already exists
    if await User.objects.filter(username=data.username).aexists():
        return 400, {"error": "Username already exists", "detail": f"User with username '{data.username}' already exists"}
    
    # Check if email already exists
    if await User.objects.filter(email=data.email).aexists():
        return 400, {"error": "Email already exists", "detail": f"User with email '{data.email}' already exists"}
    
    # Create the user
    user = await User.objects.acreate(
        username=data.username,
        email=data.email,
        first_name=data.first_name or "",
        last_name=data.last_name or "",
    )
    
    return 201, user


# Mock post data (since we don't have a Post model)
MOCK_POSTS = [
    {
        "id": 1,
        "title": "Welcome to Async Djapy",
        "content": "This is a sample post created with async Djapy!",
        "author_id": 1,
        "created_at": "2024-01-01T12:00:00Z"
    },
    {
        "id": 2,
        "title": "Getting Started with Async",
        "content": "Learn how to use async Djapy for building high-performance Django APIs with automatic OpenAPI documentation.",
        "author_id": 1,
        "created_at": "2024-01-02T12:00:00Z"
    }
]


@async_djapify(
    method='GET',
    tags=['posts']
)
async def list_posts(request) -> List[PostResponseSchema]:
    """List all posts (async)."""
    # Simulate async operation
    await sync_to_async(lambda: None)()
    return MOCK_POSTS


@async_djapify(
    method='POST',
    tags=['posts']
)
async def create_post(request, data: PostCreateSchema) -> {201: PostResponseSchema, 400: ErrorResponseSchema}:
    """Create a new post (async)."""
    from datetime import datetime
    
    # Check if author exists
    try:
        await User.objects.aget(id=data.author_id)
    except User.DoesNotExist:
        return 400, {"error": "Author not found", "detail": f"No user found with ID {data.author_id}"}
    
    # Create new post (mock implementation)
    new_post = {
        "id": len(MOCK_POSTS) + 1,
        "title": data.title,
        "content": data.content,
        "author_id": data.author_id,
        "created_at": datetime.now().isoformat() + "Z"
    }
    
    # Simulate async database operation
    await sync_to_async(MOCK_POSTS.append)(new_post)
    
    return 201, new_post


@async_djapify(
    method='GET',
    tags=['general']
)
async def trigger_message_error(request) -> {404: ErrorResponseSchema}:
    """Endpoint to demonstrate MsgErr triggering."""
    raise MsgErr("This is a test error message!", alias="test_error")


@async_djapify(
    method='GET',
    tags=['general']
)
async def trigger_custom_message(request, error_type: str = "info") -> {404: ErrorResponseSchema}:
    """Endpoint to demonstrate different types of MsgErr messages."""
    if error_type == "validation":
        raise MsgErr(
            "Validation failed: Invalid input data", 
            alias="validation_error",
            message_type="error",
            inline={"field": "Invalid value provided"}
        )
    elif error_type == "permission":
        raise MsgErr(
            "Permission denied: You don't have access to this resource", 
            alias="permission_error",
            message_type="error",
            action={"type": "redirect", "url": "/login"}
        )
    elif error_type == "server":
        raise MsgErr(
            "Internal server error occurred", 
            alias="server_error",
            message_type="error"
        )
    elif error_type == "success":
        raise MsgErr(
            "Operation completed successfully!", 
            alias="success_message",
            message_type="success"
        )
    elif error_type == "warning":
        raise MsgErr(
            "This is a warning message", 
            alias="warning_message",
            message_type="warning"
        )
    else:
        raise MsgErr(
            "This is an informational message", 
            alias="info_message",
            message_type="info"
        )