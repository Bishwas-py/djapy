# 📝 Djapy Todo API Example

Complete Todo API demonstrating all djapy v0.3.0 features and performance improvements.

## 🎯 Features Demonstrated

### **Performance Features**
- ✅ Fast JSON parsing with `model_validate_json()`
- ✅ TypeAdapter caching for 3-5x faster validation
- ✅ OpenAPI schema caching (20x faster)
- ✅ `model_dump_fast()` for internal operations
- ✅ `orjson` support for 5x faster JSON encoding
- ✅ LRU caching for schema operations

### **Pydantic V2 Features**
- ✅ `@computed_field` for dynamic calculated fields
- ✅ `@model_serializer` for custom JSON serialization
- ✅ `@field_validator` for field-level validation
- ✅ Nested schemas with relationships
- ✅ Pattern validation (regex)
- ✅ Custom validators

### **Django Features**
- ✅ Efficient queries with `select_related` and `prefetch_related`
- ✅ Django caching with `@cache_page`
- ✅ Bulk operations (`abulk_create`)
- ✅ Complex filtering with Q objects
- ✅ M2M relationships

### **API Features**
- ✅ Full CRUD operations
- ✅ Async endpoints with `@async_djapify`
- ✅ Bulk operations
- ✅ Statistics and analytics
- ✅ Advanced filtering
- ✅ Multiple response status codes
- ✅ OpenAPI/Swagger documentation

---

## 🚀 Quick Start

### 1. Setup

```bash
# Navigate to example directory
cd examples/todo

# Create virtual environment (or use project's venv)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django pydantic

# Or install with performance package
pip install 'djapy[performance]'  # Includes orjson
```

### 2. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create some test data (optional)
python manage.py shell
```

```python
# In Django shell
from django.contrib.auth.models import User
from todo_api.models import Todo, Tag

# Create user
user = User.objects.create_user('demo', 'demo@example.com', 'password')

# Create tags
tag1 = Tag.objects.create(name='work', color='#3B82F6')
tag2 = Tag.objects.create(name='personal', color='#10B981')

# Create todos
todo1 = Todo.objects.create(
    title='Test djapy features',
    description='Try all the new performance improvements',
    priority='high',
    owner=user
)
todo1.tags.add(tag1)

todo2 = Todo.objects.create(
    title='Write documentation',
    priority='medium',
    owner=user
)
todo2.tags.add(tag1, tag2)
```

### 3. Run Server

```bash
python manage.py runserver
```

---

## 📚 API Endpoints

### **Todos**
- `GET /api/todos/` - List todos (with filtering)
- `POST /api/todos/create/` - Create todo
- `GET /api/todos/{id}/` - Get todo details
- `PUT /api/todos/{id}/update/` - Update todo
- `DELETE /api/todos/{id}/delete/` - Delete todo

### **Async Operations**
- `GET /api/todos/async/` - Async list todos
- `POST /api/todos/bulk-create/` - Bulk create todos

### **Statistics**
- `GET /api/stats/` - Get todo statistics (cached)

### **Tags**
- `GET /api/tags/` - List tags
- `POST /api/tags/create/` - Create tag

### **Comments**
- `POST /api/todos/{id}/comments/` - Add comment

### **Performance Tests**
- `GET /api/test/serialization/?count=100` - Test serialization performance

### **Documentation**
- `GET /docs/` - Swagger UI
- `GET /docs/openapi.json` - OpenAPI schema

---

## 🧪 Testing the API

### **1. List Todos**
```bash
curl http://localhost:8000/api/todos/
```

### **2. Create Todo**
```bash
curl -X POST http://localhost:8000/api/todos/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Todo",
    "description": "Testing djapy",
    "priority": "high",
    "tag_ids": [1]
  }'
```

### **3. Filter Todos**
```bash
# By completion status
curl "http://localhost:8000/api/todos/?completed=false"

# By priority
curl "http://localhost:8000/api/todos/?priority=high"

# Search
curl "http://localhost:8000/api/todos/?search=test"
```

### **4. Get Statistics**
```bash
curl http://localhost:8000/api/stats/
```

### **5. Test Performance**
```bash
# Test serialization with 100 items
curl "http://localhost:8000/api/test/serialization/?count=100"

# Response shows:
# {
#   "count": 100,
#   "standard_ms": 45.23,
#   "fast_ms": 18.92,
#   "improvement": "2.39x faster"
# }
```

### **6. Bulk Create (Async)**
```bash
curl -X POST http://localhost:8000/api/todos/bulk-create/ \
  -H "Content-Type: application/json" \
  -d '[
    {"title": "Todo 1", "priority": "low"},
    {"title": "Todo 2", "priority": "medium"},
    {"title": "Todo 3", "priority": "high"}
  ]'
```

---

## 📖 Key Code Examples

### **1. Computed Fields**
```python
class TodoSchema(Schema):
    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Dynamically calculated"""
        if not self.due_date or self.completed:
            return False
        return datetime.now() > self.due_date

    @computed_field
    @property
    def status(self) -> str:
        """Derived from multiple fields"""
        if self.completed:
            return 'completed'
        if self.is_overdue:
            return 'overdue'
        return 'in_progress'
```

### **2. Custom Serialization**
```python
@model_serializer(mode='wrap', when_used='json')
def _serialize(self, serializer, info):
    """Custom JSON output"""
    data = serializer(self)
    # Add computed summary
    data['summary'] = f"{self.title} ({self.status})"
    # Add priority color
    data['priority_color'] = PRIORITY_COLORS[self.priority]
    return data
```

### **3. Field Validation**
```python
@field_validator('due_date')
@classmethod
def validate_due_date(cls, v):
    """Ensure due date is in future"""
    if v and v < datetime.now():
        raise ValueError('Due date must be in the future')
    return v
```

### **4. Async Views**
```python
@async_djapify(method="GET")
async def list_todos_async(request) -> List[TodoSchema]:
    """Fast async endpoint"""
    queryset = Todo.objects.all()
    todos = []
    async for todo in queryset:
        todos.append(todo)
    return todos
```

---

## 🎯 Performance Benchmarks

Run the built-in performance tests:

```bash
# Test with 100 items
curl "http://localhost:8000/api/test/serialization/?count=100"

# Test with 1000 items
curl "http://localhost:8000/api/test/serialization/?count=1000"
```

**Expected Results:**
- **100 items**: `model_dump_fast()` is ~2-3x faster
- **1000 items**: `model_dump_fast()` is ~2-4x faster
- **With orjson**: Additional 3-5x improvement

---

## 🔍 Exploring Features

### **1. Check Swagger Docs**
Open http://localhost:8000/docs/ to see:
- All endpoints documented
- Request/response schemas
- Try API directly from browser

### **2. Inspect Computed Fields**
```bash
curl http://localhost:8000/api/todos/1/
```
Notice the computed fields in response:
- `is_overdue`
- `status`
- `completion_percentage`
- `summary`
- `priority_color`

### **3. Test Caching**
```bash
# First request (slow)
time curl http://localhost:8000/api/stats/

# Second request (cached, fast)
time curl http://localhost:8000/api/stats/
```

---

## 🎓 Learning Points

### **1. Fast JSON Parsing**
- djapy automatically uses `model_validate_json()` for request body
- This bypasses Python dict conversion
- **Result**: 2-3x faster request parsing

### **2. TypeAdapter Caching**
- Parsers cache TypeAdapters per request
- Reduces repeated `create_model()` calls
- **Result**: Better memory usage and speed

### **3. Multiple Serialization Modes**
```python
# For JSON responses
data = schema.model_dump(mode='json')

# For internal operations (faster)
data = schema.model_dump_fast()  # mode='python'
```

### **4. OpenAPI Caching**
- Schema cached with Django cache backend
- Hash-based cache invalidation
- **Result**: 20x faster schema generation

---

## 📝 Notes

- This is a demo project, not production-ready
- Uses `owner_id=1` for simplicity
- No authentication required (for testing)
- SQLite database (sufficient for demo)

---

## 🤝 Contributing

Found an issue or want to improve the example? PRs welcome!

---

**Happy coding with djapy! 🚀**
