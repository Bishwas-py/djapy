"""
Schemas for Todo API demonstrating all djapy/Pydantic V2 features
"""
from datetime import datetime
from typing import Optional, List
from pydantic import (
    Field,
    computed_field,
    model_serializer,
    field_validator,
    ConfigDict
)
from pydantic_core.core_schema import SerializationInfo

from djapy import Schema
from djapy.schema.schema import QueryList


# ============================================================================
# Tag Schemas
# ============================================================================

class TagSchema(Schema):
    """Tag schema with validation"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field(
        default="#3B82F6",
        pattern=r'^#[0-9A-Fa-f]{6}$',
        description="Hex color code"
    )
    created_at: Optional[datetime] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Normalize tag name"""
        return v.strip().lower()


class TagCreateSchema(Schema):
    """Schema for creating tags"""
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#3B82F6", pattern=r'^#[0-9A-Fa-f]{6}$')


# ============================================================================
# Comment Schemas
# ============================================================================

class CommentAuthorSchema(Schema):
    """Nested author schema"""
    id: int
    username: str
    email: str


class CommentSchema(Schema):
    """Comment schema with nested author"""
    id: Optional[int] = None
    content: str = Field(..., min_length=1, description="Comment content")
    author: Optional[CommentAuthorSchema] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CommentCreateSchema(Schema):
    """Schema for creating comments"""
    content: str = Field(..., min_length=1, max_length=1000)


# ============================================================================
# Todo Schemas - Demonstrating Advanced Features
# ============================================================================

class TodoBaseSchema(Schema):
    """Base todo schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Todo title")
    description: str = Field(default='', description="Detailed description")
    completed: bool = Field(default=False, description="Completion status")
    priority: str = Field(
        default='medium',
        pattern=r'^(low|medium|high|urgent)$',
        description="Priority level"
    )


class TodoCreateSchema(TodoBaseSchema):
    """Schema for creating todos"""
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)
    tag_ids: List[int] = Field(default_factory=list, description="Tag IDs to attach")

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure due date is in the future"""
        if v and v < datetime.now(v.tzinfo):
            raise ValueError('Due date must be in the future')
        return v


class TodoUpdateSchema(Schema):
    """Schema for updating todos - all fields optional"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern=r'^(low|medium|high|urgent)$')
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)
    actual_hours: Optional[float] = Field(None, ge=0, le=1000)
    tag_ids: Optional[List[int]] = None


class TodoSchema(TodoBaseSchema):
    """
    Full todo schema demonstrating advanced Pydantic V2 features:
    - computed_field: Dynamic calculated fields
    - model_serializer: Custom serialization
    - Nested relationships
    """
    id: int
    owner_id: int
    tags: QueryList[TagSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None

    # Computed fields - calculated dynamically
    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if todo is overdue"""
        if not self.due_date or self.completed:
            return False
        return datetime.now(self.due_date.tzinfo) > self.due_date

    @computed_field
    @property
    def completion_percentage(self) -> Optional[float]:
        """Calculate completion percentage based on hours"""
        if not self.estimated_hours or not self.actual_hours:
            return None
        percentage = (self.actual_hours / self.estimated_hours) * 100
        return min(percentage, 100.0)  # Cap at 100%

    @computed_field
    @property
    def status(self) -> str:
        """Derive status from various fields"""
        if self.completed:
            return 'completed'
        if self.is_overdue:
            return 'overdue'
        if self.due_date and (self.due_date - datetime.now(self.due_date.tzinfo)).days <= 1:
            return 'due_soon'
        return 'in_progress'

    # Custom serialization
    @model_serializer(mode='wrap', when_used='json')
    def _serialize(self, serializer, info: SerializationInfo):
        """
        Custom JSON serialization demonstrating Pydantic V2 features
        This runs only when serializing to JSON
        """
        data = serializer(self)
        
        # Add computed summary field
        data['summary'] = f"{self.title} ({self.status})"
        
        # Format dates consistently
        if 'created_at' in data:
            data['created_at'] = data['created_at']
        
        # Add priority color for frontend
        priority_colors = {
            'low': '#10B981',      # Green
            'medium': '#3B82F6',   # Blue
            'high': '#F59E0B',     # Orange
            'urgent': '#EF4444',   # Red
        }
        data['priority_color'] = priority_colors.get(self.priority, '#6B7280')
        
        return data


class TodoDetailSchema(TodoSchema):
    """Extended todo schema with comments"""
    comments: QueryList[CommentSchema] = Field(default_factory=list)
    owner: Optional[CommentAuthorSchema] = None

    @computed_field
    @property
    def comment_count(self) -> int:
        """Get comment count"""
        return len(self.comments)


# ============================================================================
# Bulk Operations
# ============================================================================

class BulkUpdateSchema(Schema):
    """Schema for bulk updating todos"""
    todo_ids: List[int] = Field(..., min_length=1, description="Todo IDs to update")
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern=r'^(low|medium|high|urgent)$')
    tag_ids: Optional[List[int]] = None


# ============================================================================
# Statistics & Analytics
# ============================================================================

class TodoStatsSchema(Schema):
    """
    Statistics schema demonstrating model_dump_fast usage
    This is optimized for internal calculations
    """
    total: int = 0
    completed: int = 0
    in_progress: int = 0
    overdue: int = 0
    by_priority: dict = Field(default_factory=dict)
    by_tag: dict = Field(default_factory=dict)

    @computed_field
    @property
    def completion_rate(self) -> float:
        """Calculate completion rate"""
        if self.total == 0:
            return 0.0
        return round((self.completed / self.total) * 100, 2)


# ============================================================================
# Response Wrappers
# ============================================================================

class TodoListResponse(Schema):
    """Paginated todo list response"""
    items: List[TodoSchema]
    total: int
    page: int = 1
    page_size: int = 10
    has_next: bool = False


class MessageSchema(Schema):
    """Generic message response"""
    message: str
    detail: Optional[str] = None


class ErrorSchema(Schema):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    field: Optional[str] = None
