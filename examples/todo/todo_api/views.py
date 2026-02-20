"""
Todo API Views - Demonstrating all djapy improvements and Pydantic V2 features
"""
from typing import List, Optional
from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Q, Count, Prefetch
from django.views.decorators.cache import cache_page

from djapy import djapify, async_djapify
from djapy.pagination import paginate, OffsetLimitPagination, PageNumberPagination, CursorPagination

from .models import Todo, Tag, Comment
from .schemas import (
    TodoSchema, TodoDetailSchema, TodoCreateSchema, TodoUpdateSchema,
    TodoStatsSchema, TagSchema, TagCreateSchema, CommentSchema,
    CommentCreateSchema, BulkUpdateSchema, MessageSchema, ErrorSchema,
)

TAGS = ['todos']
CACHE_TTL = 300


# ============================================================================
# Todo CRUD Operations
# ============================================================================

@djapify(method="GET", tags=TAGS)
@paginate(OffsetLimitPagination)
def list_todos(
    request,
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
) -> List[TodoSchema]:
    """
    List todos with filtering and pagination
    
    Demonstrates:
    - Offset/limit pagination with computed fields
    - Efficient querying with select_related
    - Query parameter filtering
    """
    queryset = Todo.objects.select_related('owner').prefetch_related('tags')
    
    if completed is not None:
        queryset = queryset.filter(completed=completed)
    if priority:
        queryset = queryset.filter(priority=priority)
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
    
    return queryset


@djapify(method="POST", tags=TAGS)
def create_todo(request, data: TodoCreateSchema) -> {201: TodoSchema, 400: ErrorSchema}:
    """Create a new todo"""
    try:
        todo = Todo.objects.create(
            title=data.title,
            description=data.description,
            completed=data.completed,
            priority=data.priority,
            due_date=data.due_date,
            estimated_hours=data.estimated_hours,
            owner_id=1
        )
        if data.tag_ids:
            todo.tags.set(data.tag_ids)
        todo.refresh_from_db()
        return 201, todo
    except Exception as e:
        return 400, {"error": "Failed to create todo", "detail": str(e)}


@djapify(method="GET", tags=TAGS)
def get_todo(request, todo_id: int) -> {200: TodoDetailSchema, 404: ErrorSchema}:
    """Get a single todo with details"""
    try:
        todo = Todo.objects.select_related('owner').prefetch_related(
            'tags',
            Prefetch('comments', queryset=Comment.objects.select_related('author'))
        ).get(id=todo_id)
        return todo
    except Todo.DoesNotExist:
        return 404, {"error": "Todo not found"}


@djapify(method="PUT", tags=TAGS)
def update_todo(request, todo_id: int, data: TodoUpdateSchema) -> {200: TodoSchema, 404: ErrorSchema}:
    """Update a todo"""
    try:
        todo = Todo.objects.get(id=todo_id)
        update_data = data.model_dump(exclude_unset=True)
        tag_ids = update_data.pop('tag_ids', None)
        
        for field, value in update_data.items():
            setattr(todo, field, value)
        todo.save()
        
        if tag_ids is not None:
            todo.tags.set(tag_ids)
        
        todo.refresh_from_db()
        return todo
    except Todo.DoesNotExist:
        return 404, {"error": "Todo not found"}


@djapify(method="DELETE", tags=TAGS)
def delete_todo(request, todo_id: int) -> {204: MessageSchema, 404: ErrorSchema}:
    """Delete a todo"""
    try:
        todo = Todo.objects.get(id=todo_id)
        todo.delete()
        return 204, {"message": "Todo deleted"}
    except Todo.DoesNotExist:
        return 404, {"error": "Todo not found"}


# ============================================================================
# Async Operations
# ============================================================================

@async_djapify(method="GET", tags=['async'])
@paginate(PageNumberPagination)
async def list_todos_async(request, completed: Optional[bool] = None) -> List[TodoSchema]:
    """
    Async list todos with page number pagination
    
    Demonstrates:
    - Async pagination
    - Page number based pagination
    - Computed fields (items_count, start_index, etc.)
    """
    queryset = Todo.objects.select_related('owner').prefetch_related('tags')
    if completed is not None:
        queryset = queryset.filter(completed=completed)
    
    return queryset


@async_djapify(method="POST", tags=['async'])
async def bulk_create_todos(request, data: List[TodoCreateSchema]) -> {201: List[TodoSchema]}:
    """Bulk create todos"""
    todos = [
        Todo(
            title=item.title, description=item.description,
            completed=item.completed, priority=item.priority,
            due_date=item.due_date, estimated_hours=item.estimated_hours,
            owner_id=1
        )
        for item in data
    ]
    created_todos = await Todo.objects.abulk_create(todos)
    return 201, created_todos


# ============================================================================
# Statistics
# ============================================================================

@cache_page(CACHE_TTL)
@djapify(method="GET", tags=['stats'])
def get_todo_stats(request) -> TodoStatsSchema:
    """Get todo statistics"""
    total = Todo.objects.count()
    completed = Todo.objects.filter(completed=True).count()
    overdue = Todo.objects.filter(completed=False, due_date__lt=datetime.now()).count()
    
    priority_stats = dict(
        Todo.objects.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
    )
    
    tag_stats = dict(
        Tag.objects.annotate(todo_count=Count('todos')).values_list('name', 'todo_count')
    )
    
    return TodoStatsSchema(
        total=total,
        completed=completed,
        in_progress=total - completed,
        overdue=overdue,
        by_priority=priority_stats,
        by_tag=tag_stats
    )


# ============================================================================
# Tags & Comments
# ============================================================================

@djapify(method="GET", tags=['tags'])
def list_tags(request) -> List[TagSchema]:
    """List all tags"""
    return list(Tag.objects.all())


@djapify(method="POST", tags=['tags'])
def create_tag(request, data: TagCreateSchema) -> {201: TagSchema, 400: ErrorSchema}:
    """Create a tag"""
    try:
        tag = Tag.objects.create(name=data.name, color=data.color)
        return 201, tag
    except Exception as e:
        return 400, {"error": "Failed to create tag", "detail": str(e)}


@djapify(method="POST", tags=['comments'])
def add_comment(request, todo_id: int, data: CommentCreateSchema) -> {201: CommentSchema, 404: ErrorSchema}:
    """Add comment to todo"""
    try:
        todo = Todo.objects.get(id=todo_id)
        comment = Comment.objects.create(todo=todo, author_id=1, content=data.content)
        comment = Comment.objects.select_related('author').get(id=comment.id)
        return 201, comment
    except Todo.DoesNotExist:
        return 404, {"error": "Todo not found"}


# ============================================================================
# Performance Tests
# ============================================================================

@djapify(method="GET", tags=['performance'])
def test_serialization(request, count: int = 100) -> dict:
    """Test serialization performance"""
    import time
    
    todos = list(Todo.objects.select_related('owner').prefetch_related('tags')[:count])
    
    start = time.perf_counter()
    schemas = [TodoSchema.model_validate(todo) for todo in todos]
    [s.model_dump(mode='json') for s in schemas]
    standard_time = time.perf_counter() - start
    
    start = time.perf_counter()
    schemas = [TodoSchema.model_validate(todo) for todo in todos]
    [s.model_dump_fast() for s in schemas]
    fast_time = time.perf_counter() - start
    
    return {
        "count": count,
        "standard_ms": round(standard_time * 1000, 2),
        "fast_ms": round(fast_time * 1000, 2),
        "improvement": f"{round(standard_time / fast_time, 2)}x faster"
    }