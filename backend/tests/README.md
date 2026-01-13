# Backend Tests

## Overview

Tests for the FastAPI backend focus on:

1. **API Endpoints** (`test_main.py`): Tests for all public API routes including:
   - Health check endpoint
   - Error event creation and retrieval
   - Project management (CRUD operations)
   - User authentication and sync
   - Authorization checks

2. **Authentication** (`test_auth.py`): Tests for JWT token creation, validation, and user authentication

3. **CRUD Operations** (`test_crud.py`): Tests for database operations including:
   - Error event creation and filtering
   - Project management
   - User management
   - Data validation

4. **Schema Validation** (`test_schemas.py`): Tests for Pydantic schema validation

## Running Tests

```bash
cd backend
pytest -v
```

Tests use an in-memory SQLite database for speed and isolation. Each test gets a fresh database.
