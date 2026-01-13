"""
Tests for Pydantic schemas validation.
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas import schemas


def test_event_create_valid():
    """Test creating valid EventCreate."""
    event = schemas.EventCreate(
        project_key="test-project",
        message="Test error",
        method="GET",
        path="/test",
        timestamp=datetime.now(timezone.utc)
    )
    
    assert event.project_key == "test-project"
    assert event.message == "Test error"
    assert event.method == "GET"


def test_event_create_missing_required():
    """Test EventCreate with missing required fields."""
    with pytest.raises(ValidationError):
        schemas.EventCreate(
            project_key="test-project",
            # Missing message, method, path, timestamp
        )


def test_event_create_timestamp_parsing():
    """Test timestamp parsing in EventCreate."""
    # Test ISO string
    event = schemas.EventCreate(
        project_key="test",
        message="Test",
        method="GET",
        path="/test",
        timestamp="2024-01-01T12:00:00Z"
    )
    
    assert isinstance(event.timestamp, datetime)
    
    # Test with Z timezone
    event2 = schemas.EventCreate(
        project_key="test",
        message="Test",
        method="GET",
        path="/test",
        timestamp="2024-01-01T12:00:00+00:00"
    )
    
    assert isinstance(event2.timestamp, datetime)


def test_project_create_valid():
    """Test creating valid ProjectCreate."""
    project = schemas.ProjectCreate(
        name="Test Project",
        project_key="test-project",
        language="python",
        framework="django"
    )
    
    assert project.name == "Test Project"
    assert project.project_key == "test-project"
    assert project.language == "python"


def test_project_create_missing_required():
    """Test ProjectCreate with missing required fields."""
    with pytest.raises(ValidationError):
        schemas.ProjectCreate(
            name="Test Project"
            # Missing project_key
        )


def test_user_sync_request_valid():
    """Test creating valid UserSyncRequest."""
    user = schemas.UserSyncRequest(
        github_id="12345",
        username="testuser",
        email="test@example.com"
    )
    
    assert user.github_id == "12345"
    assert user.username == "testuser"
    assert user.email == "test@example.com"


def test_user_sync_request_missing_required():
    """Test UserSyncRequest with missing required fields."""
    with pytest.raises(ValidationError):
        schemas.UserSyncRequest(
            github_id="12345"
            # Missing username
        )
