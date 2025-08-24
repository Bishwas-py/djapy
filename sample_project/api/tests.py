import json
from django.test import TestCase, AsyncClient
from django.contrib.auth.models import User
from django.urls import reverse
from asgiref.sync import sync_to_async
from djapy_ext.exception import MsgErr


class AsyncAPITestCase(TestCase):
    """Base test case for async API endpoints"""
    
    def setUp(self):
        self.client = AsyncClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

    async def async_setUp(self):
        """Async setup for tests that need it"""
        self.client = AsyncClient()
        self.user = await User.objects.acreate(
            username='asynctestuser',
            email='asynctest@example.com',
            first_name='Async',
            last_name='User'
        )


class HelloWorldAPITest(AsyncAPITestCase):
    """Test the hello world endpoint"""
    
    async def test_hello_world_endpoint(self):
        """Test the basic hello world functionality"""
        response = await self.client.get('/api/hello/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['message'], 'Hello from Async Djapy!')
        self.assertIsNone(data['user'])  # No authenticated user


class UserAPITest(AsyncAPITestCase):
    """Test user-related endpoints"""
    
    async def test_list_users(self):
        """Test listing users with pagination"""
        response = await self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('items', data)
        self.assertIn('offset', data)
        self.assertIn('limit', data)
        self.assertIn('has_next', data)
        self.assertIn('has_previous', data)
        self.assertIn('total_pages', data)
        
        # Should have at least one user from setUp
        self.assertGreaterEqual(len(data['items']), 1)

    async def test_get_user_by_id(self):
        """Test getting a specific user by ID"""
        response = await self.client.get(f'/api/users/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')

    async def test_get_nonexistent_user(self):
        """Test getting a user that doesn't exist"""
        response = await self.client.get('/api/users/99999/')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'User not found')

    async def test_create_user_success(self):
        """Test creating a new user successfully"""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = await self.client.post(
            '/api/users/create/',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertEqual(data['username'], 'newuser')
        self.assertEqual(data['email'], 'newuser@example.com')
        self.assertTrue(data['is_active'])

    async def test_create_user_duplicate_username(self):
        """Test creating a user with duplicate username"""
        user_data = {
            'username': 'testuser',  # Already exists from setUp
            'email': 'different@example.com',
            'first_name': 'Different',
            'last_name': 'User'
        }
        
        response = await self.client.post(
            '/api/users/create/',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Username already exists')

    async def test_create_user_duplicate_email(self):
        """Test creating a user with duplicate email"""
        user_data = {
            'username': 'differentuser',
            'email': 'test@example.com',  # Already exists from setUp
            'first_name': 'Different',
            'last_name': 'User'
        }
        
        response = await self.client.post(
            '/api/users/create/',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Email already exists')


class PostAPITest(AsyncAPITestCase):
    """Test post-related endpoints"""
    
    async def test_list_posts(self):
        """Test listing posts"""
        response = await self.client.get('/api/posts/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)  # Mock data has 2 posts
        
        # Check structure of first post
        post = data[0]
        self.assertIn('id', post)
        self.assertIn('title', post)
        self.assertIn('content', post)
        self.assertIn('author_id', post)
        self.assertIn('created_at', post)

    async def test_create_post_success(self):
        """Test creating a new post successfully"""
        post_data = {
            'title': 'Test Post',
            'content': 'This is a test post content',
            'author_id': self.user.id
        }
        
        response = await self.client.post(
            '/api/posts/create/',
            data=json.dumps(post_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertEqual(data['title'], 'Test Post')
        self.assertEqual(data['content'], 'This is a test post content')
        self.assertEqual(data['author_id'], self.user.id)

    async def test_create_post_invalid_author(self):
        """Test creating a post with invalid author"""
        post_data = {
            'title': 'Test Post',
            'content': 'This is a test post content',
            'author_id': 99999  # Non-existent user
        }
        
        response = await self.client.post(
            '/api/posts/create/',
            data=json.dumps(post_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Author not found')


class MessageErrorTest(AsyncAPITestCase):
    """Test message error handling"""
    
    async def test_trigger_simple_error(self):
        """Test triggering a simple error message"""
        response = await self.client.get('/api/trigger-error/')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data['message'], 'This is a test error message!')
        self.assertEqual(data['alias'], 'test_error')

    async def test_trigger_validation_error(self):
        """Test triggering a validation error"""
        response = await self.client.get('/api/trigger-custom/?error_type=validation')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data['message'], 'Validation failed: Invalid input data')
        self.assertEqual(data['alias'], 'validation_error')
        self.assertEqual(data['message_type'], 'error')
        self.assertIn('inline', data)

    async def test_trigger_permission_error(self):
        """Test triggering a permission error"""
        response = await self.client.get('/api/trigger-custom/?error_type=permission')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data['message'], 'Permission denied: You don\'t have access to this resource')
        self.assertEqual(data['alias'], 'permission_error')
        self.assertEqual(data['message_type'], 'error')
        self.assertIn('action', data)

    async def test_trigger_success_message(self):
        """Test triggering a success message"""
        response = await self.client.get('/api/trigger-custom/?error_type=success')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data['message'], 'Operation completed successfully!')
        self.assertEqual(data['alias'], 'success_message')
        self.assertEqual(data['message_type'], 'success')

    async def test_trigger_warning_message(self):
        """Test triggering a warning message"""
        response = await self.client.get('/api/trigger-custom/?error_type=warning')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data['message'], 'This is a warning message')
        self.assertEqual(data['alias'], 'warning_message')
        self.assertEqual(data['message_type'], 'warning')

    async def test_trigger_info_message(self):
        """Test triggering an info message"""
        response = await self.client.get('/api/trigger-custom/?error_type=info')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data['message'], 'This is an informational message')
        self.assertEqual(data['alias'], 'info_message')
        self.assertEqual(data['message_type'], 'info')


class OpenAPITest(TestCase):
    """Test OpenAPI documentation generation"""
    
    def test_openapi_json_endpoint(self):
        """Test that OpenAPI JSON is generated correctly"""
        response = self.client.get('/docs/openapi.json')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['openapi'], '3.1.0')
        self.assertEqual(data['info']['title'], 'Sample Async Djapy API')
        self.assertIn('paths', data)
        self.assertIn('components', data)
        
        # Check that our endpoints are documented
        paths = data['paths']
        self.assertIn('/api/hello/', paths)
        self.assertIn('/api/users/', paths)
        self.assertIn('/api/posts/', paths)

    def test_swagger_ui_endpoint(self):
        """Test that Swagger UI is accessible"""
        response = self.client.get('/docs/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])


class SchemaValidationTest(TestCase):
    """Test Pydantic schema validation"""
    
    def test_user_create_schema_validation(self):
        """Test UserCreateSchema validation"""
        from api.schema import UserCreateSchema
        
        # Valid data
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        schema = UserCreateSchema(**valid_data)
        self.assertEqual(schema.username, 'testuser')
        
        # Invalid data - username too short
        with self.assertRaises(Exception):
            UserCreateSchema(username='ab', email='test@example.com')

    def test_post_create_schema_validation(self):
        """Test PostCreateSchema validation"""
        from api.schema import PostCreateSchema
        
        # Valid data
        valid_data = {
            'title': 'Test Post',
            'content': 'This is test content',
            'author_id': 1
        }
        schema = PostCreateSchema(**valid_data)
        self.assertEqual(schema.title, 'Test Post')
        
        # Invalid data - empty title
        with self.assertRaises(Exception):
            PostCreateSchema(title='', content='content', author_id=1)