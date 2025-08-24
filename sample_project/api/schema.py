from typing import Optional
from djapy import Schema
from pydantic import Field
from datetime import datetime


# Pydantic schemas for request/response validation
class UserCreateSchema(Schema):
    username: str = Field(..., min_length=3, max_length=50, description="Username for the new user")
    email: str = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, max_length=30, description="First name")
    last_name: Optional[str] = Field(None, max_length=30, description="Last name")


class UserResponseSchema(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    date_joined: datetime


class PostCreateSchema(Schema):
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field(..., min_length=1, description="Post content")
    author_id: int = Field(..., description="ID of the post author")


class PostResponseSchema(Schema):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime


class HelloResponseSchema(Schema):
    message: str
    timestamp: datetime
    user: Optional[str] = None


class ErrorResponseSchema(Schema):
    error: str
    detail: Optional[str] = None
