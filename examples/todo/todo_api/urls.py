"""
URL configuration for todo_api
"""
from django.urls import path
from . import views

urlpatterns = [
    # Todo CRUD
    path('todos/', views.list_todos, name='list_todos'),
    path('todos/create/', views.create_todo, name='create_todo'),
    path('todos/<int:todo_id>/', views.get_todo, name='get_todo'),
    path('todos/<int:todo_id>/update/', views.update_todo, name='update_todo'),
    path('todos/<int:todo_id>/delete/', views.delete_todo, name='delete_todo'),
    
    # Async operations
    path('todos/async/', views.list_todos_async, name='list_todos_async'),
    path('todos/bulk-create/', views.bulk_create_todos, name='bulk_create_todos'),
    
    # Statistics
    path('stats/', views.get_todo_stats, name='get_todo_stats'),
    
    # Tags
    path('tags/', views.list_tags, name='list_tags'),
    path('tags/create/', views.create_tag, name='create_tag'),
    
    # Comments
    path('todos/<int:todo_id>/comments/', views.add_comment, name='add_comment'),
    
    # Performance tests
    path('test/serialization/', views.test_serialization, name='test_serialization'),
]
