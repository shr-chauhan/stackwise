"""
Tests for authentication utilities.
"""
import pytest
from datetime import datetime, timedelta, timezone
import jwt
import os

from app.utils.auth import (
    create_access_token,
    decode_access_token,
    get_current_user
)
from app.database import models


def test_create_access_token():
    """Test JWT token creation."""
    user_id = 1
    github_id = "12345"
    
    token = create_access_token(user_id, github_id)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decode and verify
    decoded = jwt.decode(token, os.getenv("JWT_SECRET", "your-secret-key-change-in-production"), algorithms=["HS256"])
    assert decoded["sub"] == str(user_id)
    assert decoded["github_id"] == github_id
    assert "exp" in decoded
    assert "iat" in decoded


def test_decode_access_token_valid():
    """Test decoding a valid token."""
    user_id = 1
    github_id = "12345"
    
    token = create_access_token(user_id, github_id)
    decoded = decode_access_token(token)
    
    assert decoded is not None
    assert decoded["sub"] == str(user_id)
    assert decoded["github_id"] == github_id


def test_decode_access_token_invalid():
    """Test decoding an invalid token."""
    invalid_token = "invalid.token.here"
    decoded = decode_access_token(invalid_token)
    
    assert decoded is None


def test_decode_access_token_expired():
    """Test decoding an expired token."""
    # Create an expired token manually
    secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    payload = {
        "sub": "1",
        "github_id": "12345",
        "exp": datetime.now(timezone.utc) - timedelta(days=1),  # Expired yesterday
        "iat": datetime.now(timezone.utc) - timedelta(days=2)
    }
    expired_token = jwt.encode(payload, secret, algorithm="HS256")
    
    decoded = decode_access_token(expired_token)
    assert decoded is None


def test_get_current_user_valid_token(client, test_user, db):
    """Test getting current user with valid token."""
    from app.utils.auth import create_access_token
    
    token = create_access_token(test_user.id, test_user.github_id)
    
    # Override get_db dependency
    from app.database.database import get_db
    from app.main import app
    
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.security import HTTPAuthorizationCredentials
    
    # Create mock credentials
    class MockCredentials:
        def __init__(self, token):
            self.credentials = token
    
    credentials = MockCredentials(token)
    user = get_current_user(credentials, db)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.github_id == test_user.github_id
    
    app.dependency_overrides.clear()


def test_get_current_user_invalid_token(client, db):
    """Test getting current user with invalid token."""
    from app.main import app
    from app.database.database import get_db
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials
    
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    class MockCredentials:
        def __init__(self, token):
            self.credentials = token
    
    credentials = MockCredentials("invalid.token")
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials, db)
    
    assert exc_info.value.status_code == 401
    
    app.dependency_overrides.clear()
