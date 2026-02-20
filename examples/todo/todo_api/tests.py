"""
Comprehensive tests for Todo API
Tests all models, views, schemas, and djapy features
"""
import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Todo, Tag, Comment
from .schemas import (
    TodoSchema, TodoDetailSchema, TodoCreateSchema, TodoUpdateSchema,
    TodoStatsSchema, TagSchema, CommentSchema
)


class TagModelTest(TestCase):
    """Test the Tag model"""

    def setUp(self):
        self.tag = Tag.objects.create(name="urgent", color="#EF4444")

    def test_tag_creation(self):
        """Test creating a tag"""
        self.assertEqual(self.tag.name, "urgent")
        self.assertEqual(self.tag.color, "#EF4444")
        self.assertIsNotNone(self.tag.created_at)

    def test_tag_str_representation(self):
        """Test tag string representation"""
        self.assertEqual(str(self.tag), "urgent")

    def test_tag_ordering(self):
        """Test tags are ordered by name"""
        Tag.objects.create(name="work", color="#3B82F6")
        Tag.objects.create(name="personal", color="#10B981")
        
        tags = list(Tag.objects.all())
        self.assertEqual(tags[0].name, "personal")
        self.assertEqual(tags[1].name, "urgent")
        self.assertEqual(tags[2].name, "work")

    def test_tag_unique_constraint(self):
        """Test that tag names must be unique"""
        with self.assertRaises(Exception):
            Tag.objects.create(name="urgent", color="#000000")


class TodoModelTest(TestCase):
    """Test the Todo model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tag1 = Tag.objects.create(name="work", color="#3B82F6")
        self.tag2 = Tag.objects.create(name="urgent", color="#EF4444")

    def test_todo_creation(self):
        """Test creating a todo"""
        todo = Todo.objects.create(
            title="Test Todo",
            description="Test description",
            owner=self.user,
            priority="high"
        )
        self.assertEqual(todo.title, "Test Todo")
        self.assertEqual(todo.description, "Test description")
        self.assertEqual(todo.owner, self.user)
        self.assertEqual(todo.priority, "high")
        self.assertFalse(todo.completed)
        self.assertIsNotNone(todo.created_at)
        self.assertIsNotNone(todo.updated_at)

    def test_todo_str_representation(self):
        """Test todo string representation"""
        todo = Todo.objects.create(title="My Todo", owner=self.user)
        self.assertEqual(str(todo), "My Todo")

    def test_todo_with_tags(self):
        """Test adding tags to a todo"""
        todo = Todo.objects.create(title="Tagged Todo", owner=self.user)
        todo.tags.add(self.tag1, self.tag2)
        
        self.assertEqual(todo.tags.count(), 2)
        self.assertIn(self.tag1, todo.tags.all())
        self.assertIn(self.tag2, todo.tags.all())

    def test_todo_default_values(self):
        """Test default values"""
        todo = Todo.objects.create(title="Default Todo", owner=self.user)
        self.assertEqual(todo.description, '')
        self.assertFalse(todo.completed)
        self.assertEqual(todo.priority, 'medium')
        self.assertIsNone(todo.due_date)

    def test_todo_ordering(self):
        """Test todos are ordered by creation date (newest first)"""
        todo1 = Todo.objects.create(title="First", owner=self.user)
        todo2 = Todo.objects.create(title="Second", owner=self.user)
        
        todos = list(Todo.objects.all())
        self.assertEqual(todos[0], todo2)
        self.assertEqual(todos[1], todo1)

    def test_todo_cascade_delete(self):
        """Test that todos are deleted when owner is deleted"""
        todo = Todo.objects.create(title="Test", owner=self.user)
        user_id = self.user.id
        self.user.delete()
        
        self.assertFalse(Todo.objects.filter(owner_id=user_id).exists())


class CommentModelTest(TestCase):
    """Test the Comment model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.todo = Todo.objects.create(title="Test Todo", owner=self.user)

    def test_comment_creation(self):
        """Test creating a comment"""
        comment = Comment.objects.create(
            todo=self.todo,
            author=self.user,
            content="This is a test comment"
        )
        self.assertEqual(comment.todo, self.todo)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, "This is a test comment")
        self.assertIsNotNone(comment.created_at)
        self.assertIsNotNone(comment.updated_at)

    def test_comment_str_representation(self):
        """Test comment string representation"""
        comment = Comment.objects.create(
            todo=self.todo,
            author=self.user,
            content="Test"
        )
        expected = f"Comment by {self.user.username} on {self.todo.title}"
        self.assertEqual(str(comment), expected)

    def test_comment_cascade_delete(self):
        """Test that comments are deleted when todo is deleted"""
        comment = Comment.objects.create(
            todo=self.todo,
            author=self.user,
            content="Test"
        )
        todo_id = self.todo.id
        self.todo.delete()
        
        self.assertFalse(Comment.objects.filter(todo_id=todo_id).exists())


class TodoSchemaTest(TestCase):
    """Test Todo schemas and validation"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tag = Tag.objects.create(name="work", color="#3B82F6")

    def test_todo_schema_validation(self):
        """Test TodoSchema with valid data"""
        todo = Todo.objects.create(
            title="Test Todo",
            description="Description",
            owner=self.user,
            priority="high"
        )
        todo.tags.add(self.tag)
        
        schema = TodoSchema.model_validate(todo)
        self.assertEqual(schema.title, "Test Todo")
        self.assertEqual(schema.description, "Description")
        self.assertEqual(schema.priority, "high")
        self.assertFalse(schema.completed)

    def test_todo_schema_computed_fields(self):
        """Test computed fields in TodoSchema"""
        # Test is_overdue with overdue todo
        past_date = timezone.now() - timedelta(days=1)
        todo = Todo.objects.create(
            title="Overdue Todo",
            owner=self.user,
            due_date=past_date,
            completed=False
        )
        schema = TodoSchema.model_validate(todo)
        self.assertTrue(schema.is_overdue)
        self.assertEqual(schema.status, 'overdue')

        # Test is_overdue with completed todo (should not be overdue)
        todo.completed = True
        todo.save()
        schema = TodoSchema.model_validate(todo)
        self.assertFalse(schema.is_overdue)
        self.assertEqual(schema.status, 'completed')

    def test_todo_schema_completion_percentage(self):
        """Test completion_percentage computed field"""
        todo = Todo.objects.create(
            title="Test",
            owner=self.user,
            estimated_hours=10.0,
            actual_hours=5.0
        )
        schema = TodoSchema.model_validate(todo)
        self.assertEqual(schema.completion_percentage, 50.0)

        # Test with no hours
        todo2 = Todo.objects.create(title="Test2", owner=self.user)
        schema2 = TodoSchema.model_validate(todo2)
        self.assertIsNone(schema2.completion_percentage)

    def test_todo_schema_status(self):
        """Test status computed field"""
        # Test in_progress status
        todo = Todo.objects.create(title="Test", owner=self.user)
        schema = TodoSchema.model_validate(todo)
        self.assertEqual(schema.status, 'in_progress')

        # Test due_soon status
        tomorrow = timezone.now() + timedelta(hours=12)
        todo.due_date = tomorrow
        todo.save()
        schema = TodoSchema.model_validate(todo)
        self.assertEqual(schema.status, 'due_soon')

    def test_todo_create_schema_validation(self):
        """Test TodoCreateSchema validation"""
        # Valid data
        future_date = timezone.now() + timedelta(days=1)
        data = {
            'title': 'New Todo',
            'description': 'Description',
            'priority': 'high',
            'due_date': future_date,
            'estimated_hours': 5.0
        }
        schema = TodoCreateSchema(**data)
        self.assertEqual(schema.title, 'New Todo')
        self.assertEqual(schema.priority, 'high')

    def test_todo_create_schema_due_date_validation(self):
        """Test that past due dates are rejected"""
        past_date = timezone.now() - timedelta(days=1)
        with self.assertRaises(Exception):
            TodoCreateSchema(
                title='Test',
                due_date=past_date
            )

    def test_tag_schema_name_normalization(self):
        """Test tag name validation and normalization"""
        schema = TagSchema(name="  WORK  ", color="#3B82F6")
        self.assertEqual(schema.name, "work")


class TodoAPITest(TestCase):
    """Test Todo API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tag1 = Tag.objects.create(name="work", color="#3B82F6")
        self.tag2 = Tag.objects.create(name="personal", color="#10B981")

    def test_list_todos_empty(self):
        """Test listing todos when none exist"""
        response = self.client.get('/api/todos/')
        self.assertEqual(response.status_code, 200)

    def test_list_todos_with_data(self):
        """Test listing todos"""
        Todo.objects.create(title="Todo 1", owner=self.user)
        Todo.objects.create(title="Todo 2", owner=self.user, completed=True)
        
        response = self.client.get('/api/todos/')
        self.assertEqual(response.status_code, 200)

    def test_list_todos_filter_completed(self):
        """Test filtering todos by completion status"""
        Todo.objects.create(title="Todo 1", owner=self.user, completed=False)
        Todo.objects.create(title="Todo 2", owner=self.user, completed=True)
        
        response = self.client.get('/api/todos/', {'completed': 'true'})
        self.assertEqual(response.status_code, 200)

    def test_list_todos_filter_priority(self):
        """Test filtering todos by priority"""
        Todo.objects.create(title="Todo 1", owner=self.user, priority="high")
        Todo.objects.create(title="Todo 2", owner=self.user, priority="low")
        
        response = self.client.get('/api/todos/', {'priority': 'high'})
        self.assertEqual(response.status_code, 200)

    def test_list_todos_search(self):
        """Test searching todos"""
        Todo.objects.create(
            title="Buy groceries",
            description="Milk and eggs",
            owner=self.user
        )
        Todo.objects.create(
            title="Clean house",
            description="Living room",
            owner=self.user
        )
        
        response = self.client.get('/api/todos/', {'search': 'groceries'})
        self.assertEqual(response.status_code, 200)

    def test_create_todo(self):
        """Test creating a new todo"""
        data = {
            'title': 'New Todo',
            'description': 'Test description',
            'priority': 'high',
            'completed': False
        }
        response = self.client.post(
            '/api/todos/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Todo.objects.filter(title='New Todo').exists())

    def test_create_todo_with_tags(self):
        """Test creating a todo with tags"""
        data = {
            'title': 'Tagged Todo',
            'description': 'Test',
            'tag_ids': [self.tag1.id, self.tag2.id]
        }
        response = self.client.post(
            '/api/todos/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        
        todo = Todo.objects.get(title='Tagged Todo')
        self.assertEqual(todo.tags.count(), 2)

    def test_get_todo(self):
        """Test retrieving a single todo"""
        todo = Todo.objects.create(title="Test Todo", owner=self.user)
        
        response = self.client.get(f'/api/todos/{todo.id}/')
        self.assertEqual(response.status_code, 200)

    def test_get_todo_not_found(self):
        """Test retrieving non-existent todo"""
        response = self.client.get('/api/todos/99999/')
        self.assertEqual(response.status_code, 404)

    def test_update_todo(self):
        """Test updating a todo"""
        todo = Todo.objects.create(
            title="Original Title",
            owner=self.user,
            priority="low"
        )
        
        data = {
            'title': 'Updated Title',
            'priority': 'high',
            'completed': True
        }
        response = self.client.put(
            f'/api/todos/{todo.id}/update/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        todo.refresh_from_db()
        self.assertEqual(todo.title, 'Updated Title')
        self.assertEqual(todo.priority, 'high')
        self.assertTrue(todo.completed)

    def test_update_todo_partial(self):
        """Test partial update of a todo"""
        todo = Todo.objects.create(
            title="Test Todo",
            owner=self.user,
            description="Original description"
        )
        
        data = {'completed': True}
        response = self.client.put(
            f'/api/todos/{todo.id}/update/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        todo.refresh_from_db()
        self.assertTrue(todo.completed)
        self.assertEqual(todo.title, "Test Todo")  # Unchanged

    def test_update_todo_not_found(self):
        """Test updating non-existent todo"""
        data = {'title': 'Updated'}
        response = self.client.put(
            '/api/todos/99999/update/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_todo(self):
        """Test deleting a todo"""
        todo = Todo.objects.create(title="To Delete", owner=self.user)
        todo_id = todo.id
        
        response = self.client.delete(f'/api/todos/{todo_id}/delete/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_delete_todo_not_found(self):
        """Test deleting non-existent todo"""
        response = self.client.delete('/api/todos/99999/delete/')
        self.assertEqual(response.status_code, 404)


class TagAPITest(TestCase):
    """Test Tag API endpoints"""

    def setUp(self):
        self.client = Client()

    def test_list_tags(self):
        """Test listing all tags"""
        Tag.objects.create(name="work", color="#3B82F6")
        Tag.objects.create(name="personal", color="#10B981")
        
        response = self.client.get('/api/tags/')
        self.assertEqual(response.status_code, 200)

    def test_create_tag(self):
        """Test creating a new tag"""
        data = {
            'name': 'urgent',
            'color': '#EF4444'
        }
        response = self.client.post(
            '/api/tags/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Tag.objects.filter(name='urgent').exists())

    def test_create_tag_duplicate(self):
        """Test creating a duplicate tag fails"""
        Tag.objects.create(name="work", color="#3B82F6")
        
        data = {'name': 'work', 'color': '#000000'}
        response = self.client.post(
            '/api/tags/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class CommentAPITest(TestCase):
    """Test Comment API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.todo = Todo.objects.create(title="Test Todo", owner=self.user)

    def test_add_comment(self):
        """Test adding a comment to a todo"""
        data = {'content': 'This is a test comment'}
        response = self.client.post(
            f'/api/todos/{self.todo.id}/comments/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Comment.objects.filter(todo=self.todo).exists())

    def test_add_comment_to_nonexistent_todo(self):
        """Test adding comment to non-existent todo"""
        data = {'content': 'Test comment'}
        response = self.client.post(
            '/api/todos/99999/comments/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)


class StatsAPITest(TestCase):
    """Test Statistics API"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tag1 = Tag.objects.create(name="work", color="#3B82F6")
        self.tag2 = Tag.objects.create(name="personal", color="#10B981")

    def test_get_stats_empty(self):
        """Test getting stats with no todos"""
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, 200)

    def test_get_stats_with_data(self):
        """Test getting stats with todos"""
        # Create various todos
        todo1 = Todo.objects.create(
            title="Todo 1",
            owner=self.user,
            completed=True,
            priority="high"
        )
        todo2 = Todo.objects.create(
            title="Todo 2",
            owner=self.user,
            completed=False,
            priority="high"
        )
        todo3 = Todo.objects.create(
            title="Todo 3",
            owner=self.user,
            completed=False,
            priority="low",
            due_date=timezone.now() - timedelta(days=1)
        )
        
        todo1.tags.add(self.tag1)
        todo2.tags.add(self.tag1, self.tag2)
        
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, 200)

    def test_stats_schema_completion_rate(self):
        """Test completion rate calculation in stats schema"""
        schema = TodoStatsSchema(total=10, completed=7)
        self.assertEqual(schema.completion_rate, 70.0)
        
        # Test with zero todos
        schema_empty = TodoStatsSchema(total=0, completed=0)
        self.assertEqual(schema_empty.completion_rate, 0.0)


class AsyncAPITest(TestCase):
    """Test async API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_list_todos_async(self):
        """Test async list todos endpoint"""
        Todo.objects.create(title="Todo 1", owner=self.user)
        Todo.objects.create(title="Todo 2", owner=self.user)
        
        response = self.client.get('/api/todos/async/')
        self.assertEqual(response.status_code, 200)

    def test_bulk_create_todos(self):
        """Test bulk creating todos"""
        # Wrap in "data" key as expected by the view parameter name
        payload = {
            "data": [
                {
                    'title': 'Todo 1',
                    'description': 'First todo',
                    'priority': 'high'
                },
                {
                    'title': 'Todo 2',
                    'description': 'Second todo',
                    'priority': 'low'
                }
            ]
        }
        response = self.client.post(
            '/api/todos/bulk-create/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Todo.objects.count(), 2)


class PaginationTest(TestCase):
    """Test pagination functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create 25 todos for pagination testing
        for i in range(25):
            Todo.objects.create(
                title=f"Todo {i}",
                owner=self.user,
                priority="medium"
            )

    def test_offset_pagination(self):
        """Test offset/limit pagination"""
        response = self.client.get('/api/todos/', {'limit': 10, 'offset': 0})
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/api/todos/', {'limit': 10, 'offset': 10})
        self.assertEqual(response.status_code, 200)

    def test_page_number_pagination(self):
        """Test page number pagination"""
        response = self.client.get('/api/todos/async/', {'page': 1, 'page_size': 10})
        self.assertEqual(response.status_code, 200)


class PerformanceTest(TestCase):
    """Test performance endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create some todos for performance testing
        for i in range(50):
            Todo.objects.create(title=f"Todo {i}", owner=self.user)

    def test_serialization_performance(self):
        """Test serialization performance endpoint"""
        response = self.client.get('/api/test/serialization/', {'count': 20})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('count', data)
        self.assertIn('standard_ms', data)
        self.assertIn('fast_ms', data)
        self.assertIn('improvement', data)


class EdgeCasesTest(TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_todo_with_invalid_priority(self):
        """Test creating todo with invalid priority"""
        data = {
            'title': 'Test',
            'priority': 'invalid_priority'
        }
        response = self.client.post(
            '/api/todos/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_create_todo_with_empty_title(self):
        """Test creating todo with empty title"""
        data = {'title': ''}
        response = self.client.post(
            '/api/todos/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_create_todo_with_invalid_json(self):
        """Test creating todo with invalid JSON"""
        response = self.client.post(
            '/api/todos/create/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 422])

    def test_todo_with_extreme_hours(self):
        """Test todo with extreme estimated/actual hours"""
        todo = Todo.objects.create(
            title="Test",
            owner=self.user,
            estimated_hours=1000.0,
            actual_hours=1200.0  # Over 100%
        )
        schema = TodoSchema.model_validate(todo)
        # Should be capped at 100%
        self.assertEqual(schema.completion_percentage, 100.0)

    def test_tag_color_validation(self):
        """Test tag color validation"""
        # Valid color
        tag = TagSchema(name="test", color="#FF0000")
        self.assertEqual(tag.color, "#FF0000")
        
        # Invalid color format should raise validation error
        with self.assertRaises(Exception):
            TagSchema(name="test", color="red")  # Not hex format
        
        with self.assertRaises(Exception):
            TagSchema(name="test", color="#FFF")  # Wrong length

    def test_comment_min_length(self):
        """Test comment content minimum length"""
        with self.assertRaises(Exception):
            CommentSchema(content="")  # Empty content

    def test_multiple_tags_on_todo(self):
        """Test adding multiple tags to a todo"""
        todo = Todo.objects.create(title="Test", owner=self.user)
        tags = [Tag.objects.create(name=f"tag{i}", color="#3B82F6") for i in range(5)]
        todo.tags.set(tags)
        
        schema = TodoSchema.model_validate(todo)
        self.assertEqual(len(schema.tags), 5)
