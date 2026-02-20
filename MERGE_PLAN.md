# Branch Merge Plan: `feat/strict-typeness` → `upgrade/to-pydantic-v2`

## Overview

We need to merge critical features from `feat/strict-typeness` into `upgrade/to-pydantic-v2` to combine:
- **Pydantic V2 performance improvements** (from upgrade/to-pydantic-v2)
- **Strict type handling & better payload parsing** (from feat/strict-typeness)

---

## Key Features from `feat/strict-typeness`

### 1. **Enhanced Return Type Parsing** 🎯

**File**: `djapy/core/parser.py`

**New Functions**:
```python
def parse_tuple_annotation(annotation) -> Dict[int, Type]:
    """Parse return type annotations into status code -> schema mapping."""
    # Handles: tuple[int, Schema], Union[tuple[...], tuple[...]], etc.
    
def is_typing_type(annotation) -> bool:
    """Reliably detect if an annotation is a typing type"""
    
def prepare_schema(raw_schema) -> Dict[int, Type]:
    """Prepare schema for response parsing"""
```

**Benefits**:
- ✅ Better type inference for return annotations
- ✅ Support for complex Union types
- ✅ Cleaner tuple-based status code definitions
- ✅ More robust type checking

**Example Usage**:
```python
@djapify(method="POST")
def create_user(request, data: UserSchema) -> tuple[201, UserSchema] | tuple[400, ErrorSchema]:
    # Automatically parses into {201: UserSchema, 400: ErrorSchema}
    ...
```

---

### 2. **Payload Type Specification** 📦

**New File**: `djapy/schema/param_loadable.py`

**Features**:
```python
from djapy.schema import as_json, as_form

@djapify(method="POST")
def upload_file(request, file_data: as_form[FileSchema], metadata: as_json[MetadataSchema]):
    # file_data comes from multipart/form-data
    # metadata comes from JSON body
    ...
```

**Classes**:
- `AsJson[T]` - Explicitly marks parameter as JSON payload
- `AsForm[T]` - Explicitly marks parameter as form data
- `is_payload_type()` - Helper to detect payload types

**Benefits**:
- ✅ Explicit control over where data comes from
- ✅ Support for mixed content types in single endpoint
- ✅ Better OpenAPI documentation
- ✅ Clear separation of concerns

---

### 3. **Improved Schema Handling** 🔧

**File**: `djapy/schema/handle.py`

**Changes**:
- Better detection of Schema types
- Support for `param_loadable` types
- Cleaner enum handling
- Reduced complexity in type checking

---

### 4. **Enhanced RequestParser** 📥

**File**: `djapy/core/parser.py`

**Changes**:
```python
class RequestParser(BaseParser):
    def parse_data(self) -> dict:
        # Uses validate_via_request() instead of model_validate()
        # Better handles payload types (as_json, as_form)
        # Returns validated.__dict__ instead of model_dump()
```

**Benefits**:
- ✅ Respects `cvar_c_type` from payload annotations
- ✅ Better integration with Schema.validate_via_request()
- ✅ More consistent with Schema's single() method

---

### 5. **Sample Project with Tests** 🧪

**New Directory**: `sample_project/`

**Contains**:
- Complete Django project setup
- Comprehensive test suite (336 tests!)
- Example API endpoints
- Fixtures for testing
- Makefile for common tasks

**Test Coverage**:
- Request/response parsing
- Payload type handling
- Schema validation
- Error handling
- OpenAPI generation

---

## Merge Strategy

### Option 1: Merge feat/strict-typeness into upgrade/to-pydantic-v2 ✅ **RECOMMENDED**

```bash
git checkout upgrade/to-pydantic-v2
git merge feat/strict-typeness
# Resolve conflicts manually
```

**Pros**:
- Preserves full git history
- Shows what conflicts need resolution
- Standard git workflow

**Cons**:
- Will have merge conflicts in parser.py
- Need to carefully review each conflict

---

### Option 2: Cherry-pick Specific Commits

```bash
git checkout upgrade/to-pydantic-v2
git cherry-pick fffce31  # make single entity a schema
git cherry-pick 768fa04  # update payload instance to use form
git cherry-pick 38b21bd  # fix: update payload instance
# ... etc
```

**Pros**:
- More control over what gets merged
- Can skip commits that cause issues

**Cons**:
- Time-consuming
- May miss dependencies between commits

---

### Option 3: Manual Port (Recommended if conflicts are severe)

1. **Keep current upgrade/to-pydantic-v2 as base**
2. **Manually port features from feat/strict-typeness**:
   - Copy `param_loadable.py` → new file
   - Merge parser.py functions carefully
   - Update imports and integration points
   - Copy sample_project/ for testing

**Pros**:
- Full control
- Can adapt strict-typeness features to Pydantic V2 optimizations
- Clean result

**Cons**:
- More manual work
- Need to understand both codebases deeply

---

## Files That Will Conflict

### High Conflict Probability:
1. **`djapy/core/parser.py`** 🔴
   - Both branches heavily modified
   - Need to merge:
     - Pydantic V2 optimizations (TypeAdapter, model_validate_json)
     - Strict type parsing (parse_tuple_annotation, is_typing_type)
     - Payload type handling (as_json, as_form)

2. **`djapy/schema/__init__.py`** 🟡
   - Need to add param_loadable exports

### Low Conflict Probability:
3. **`djapy/schema/handle.py`** 🟢
   - Mostly refactoring, should merge cleanly

4. **`.gitignore`** 🟢
   - Simple additions

---

## Recommended Merge Steps

### Step 1: Backup Current Work
```bash
git checkout upgrade/to-pydantic-v2
git branch upgrade/to-pydantic-v2-backup
```

### Step 2: Attempt Merge
```bash
git merge feat/strict-typeness --no-commit
```

### Step 3: Resolve Conflicts

**For `djapy/core/parser.py`**:
- Keep Pydantic V2 optimizations:
  - `TypeAdapter` and caching
  - `model_validate_json` for fast parsing
  - `model_dump_fast()` usage
- Add strict-typeness features:
  - `parse_tuple_annotation()`
  - `is_typing_type()`
  - `prepare_schema()`
  - Better `get_response_schema_dict()`

**For `djapy/schema/__init__.py`**:
- Add: `from .param_loadable import as_json, as_form, is_payload_type`

### Step 4: Copy New Files
```bash
# param_loadable.py should be added automatically
# But verify it's there
ls -la djapy/schema/param_loadable.py
```

### Step 5: Update RequestParser Integration
Merge the `validate_via_request()` approach with Pydantic V2 features:

```python
class RequestParser(BaseParser):
    def parse_data(self) -> dict:
        # Use Pydantic V2's fast JSON parsing
        if not self.schemas["data"].is_empty():
            body_str = self._get_body()
            if body_str:
                # Fast path with model_validate_json
                validated_data_model = self._get_type_adapter(
                    self.schemas["data"]
                ).validate_json(body_str)
                body_data = validated_data_model.model_dump_fast()
        
        # Rest stays similar
        ...
```

### Step 6: Test Everything
```bash
# Run tests from sample_project
cd sample_project
python manage.py test

# Run basic import test
python -c "from djapy import djapify, as_json, as_form; print('✅ Imports successful')"
```

### Step 7: Update Documentation
- Document `as_json` and `as_form` usage
- Update examples to show tuple return types
- Add migration guide for breaking changes

---

## Breaking Changes to Watch For

1. **Schema.validate_via_request() vs model_validate()**
   - strict-typeness uses `validate_via_request()`
   - May need to ensure compatibility with Pydantic V2

2. **Return value format**
   - strict-typeness uses `validated.__dict__`
   - pydantic-v2 uses `model_dump_fast()`
   - Need to ensure consistency

3. **Payload type handling**
   - New `as_json`, `as_form` syntax
   - Need to update documentation and examples

---

## Post-Merge Tasks

1. ✅ Run full test suite
2. ✅ Update CHANGELOG to include strict-typeness features
3. ✅ Update README with new syntax examples
4. ✅ Add migration guide
5. ✅ Test with example projects
6. ✅ Update version to 0.4.0 (major feature addition)

---

## Questions to Resolve

1. **Should we keep `validate_via_request()` or migrate to pure Pydantic V2?**
   - Recommendation: Keep validate_via_request but optimize it internally with Pydantic V2

2. **How to handle backward compatibility?**
   - Old dict return types: {200: Schema}
   - New tuple syntax: tuple[200, Schema]
   - Recommendation: Support both!

3. **Should sample_project stay in main repo or move to examples/?**
   - Recommendation: Move to `examples/sample_project/`

---

## Rollback Plan

If merge goes wrong:
```bash
git merge --abort
git checkout upgrade/to-pydantic-v2-backup
```

---

## Success Criteria

- [ ] All files merge without conflicts (or conflicts resolved)
- [ ] All tests pass
- [ ] Imports work: `from djapy import djapify, as_json, as_form`
- [ ] Example project runs
- [ ] OpenAPI generation works
- [ ] Both old and new syntax supported
- [ ] Performance improvements retained
- [ ] Documentation updated

---

**Ready to proceed?** Let me know if you want to:
1. Try automatic merge
2. Manual merge (I'll help step by step)
3. Review specific conflicts first
