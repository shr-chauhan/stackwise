"""
Tests for CRUD operations.
"""
import pytest
from datetime import datetime, timezone

from app.utils.crud import (
    create_error_event,
    get_error_event_by_id,
    get_error_events,
    create_project,
    update_project,
    get_project_by_id,
    get_projects,
    get_or_create_user,
    get_project_error_count
)
from app.schemas import schemas
from app.database import models


def test_create_error_event(db, test_project):
    """Test creating an error event."""
    event = schemas.EventCreate(
        project_key="test-project",
        message="Test error",
        stack="Error: Test\n  at test.js:1:1",
        method="GET",
        path="/test",
        status_code=500,
        timestamp=datetime.now(timezone.utc)
    )
    
    db_event = create_error_event(db, event)
    
    assert db_event.id is not None
    assert db_event.project_id == test_project.id
    assert db_event.status_code == 500
    assert db_event.payload["message"] == "Test error"
    assert db_event.payload["method"] == "GET"


def test_create_error_event_invalid_project(db):
    """Test creating event with invalid project key."""
    event = schemas.EventCreate(
        project_key="non-existent",
        message="Test error",
        method="GET",
        path="/test",
        timestamp=datetime.now(timezone.utc)
    )
    
    with pytest.raises(ValueError, match="does not exist"):
        create_error_event(db, event)


def test_get_error_event_by_id(db, test_project):
    """Test getting error event by ID."""
    # Create an event first
    event = schemas.EventCreate(
        project_key="test-project",
        message="Test error",
        method="GET",
        path="/test",
        timestamp=datetime.now(timezone.utc)
    )
    db_event = create_error_event(db, event)
    
    # Retrieve it
    retrieved = get_error_event_by_id(db, db_event.id)
    
    assert retrieved is not None
    assert retrieved.id == db_event.id
    assert retrieved.payload["message"] == "Test error"


def test_get_error_events_with_filters(db, test_user, test_project):
    """Test getting error events with filters."""
    # Create multiple events
    for i in range(3):
        event = schemas.EventCreate(
            project_key="test-project",
            message=f"Error {i}",
            method="GET",
            path=f"/test{i}",
            status_code=500 if i % 2 == 0 else 404,
            timestamp=datetime.now(timezone.utc)
        )
        create_error_event(db, event)
    
    # Test filtering by status code
    events, total = get_error_events(db, user_id=test_user.id, status_code=500)
    assert total >= 2  # At least 2 events with status 500
    
    # Test filtering by project
    events, total = get_error_events(db, user_id=test_user.id, project_key="test-project")
    assert total == 3


def test_create_project(db, test_user):
    """Test creating a project."""
    project_data = schemas.ProjectCreate(
        name="New Project",
        project_key="new-project",
        language="python",
        framework="django"
    )
    
    project = create_project(db, project_data, test_user.id)
    
    assert project.id is not None
    assert project.name == "New Project"
    assert project.project_key == "new-project"
    assert project.user_id == test_user.id


def test_create_project_duplicate_key(db, test_user, test_project):
    """Test creating project with duplicate key."""
    project_data = schemas.ProjectCreate(
        name="Another Project",
        project_key="test-project"  # Already exists
    )
    
    with pytest.raises(ValueError, match="already exists"):
        create_project(db, project_data, test_user.id)


def test_update_project(db, test_project):
    """Test updating a project."""
    update_data = schemas.ProjectUpdate(
        name="Updated Name",
        language="javascript"
    )
    
    updated = update_project(db, test_project.id, update_data, test_project.user_id)
    
    assert updated.name == "Updated Name"
    assert updated.language == "javascript"
    assert updated.project_key == test_project.project_key  # Unchanged


def test_update_project_wrong_user(db, test_user, test_project):
    """Test updating project owned by different user."""
    # Create another user
    other_user = models.User(
        github_id="99999",
        username="otheruser"
    )
    db.add(other_user)
    db.commit()
    
    update_data = schemas.ProjectUpdate(name="Hacked Name")
    
    with pytest.raises(ValueError, match="permission"):
        update_project(db, test_project.id, update_data, other_user.id)


def test_get_projects(db, test_user):
    """Test getting projects."""
    # Create multiple projects
    for i in range(3):
        project_data = schemas.ProjectCreate(
            name=f"Project {i}",
            project_key=f"project-{i}"
        )
        create_project(db, project_data, test_user.id)
    
    projects, total = get_projects(db, user_id=test_user.id)
    
    assert total >= 3
    assert len(projects) >= 3


def test_get_or_create_user_new(db):
    """Test creating a new user."""
    user = get_or_create_user(
        db,
        github_id="new123",
        username="newuser",
        email="new@example.com"
    )
    
    assert user.id is not None
    assert user.github_id == "new123"
    assert user.username == "newuser"


def test_get_or_create_user_existing(db, test_user):
    """Test getting existing user."""
    user = get_or_create_user(
        db,
        github_id=test_user.github_id,
        username="updated_username",
        email="updated@example.com"
    )
    
    assert user.id == test_user.id
    assert user.username == "updated_username"  # Should be updated
    assert user.email == "updated@example.com"


def test_get_project_error_count(db, test_project):
    """Test getting error count for a project."""
    # Create some events
    for i in range(5):
        event = schemas.EventCreate(
            project_key="test-project",
            message=f"Error {i}",
            method="GET",
            path="/test",
            timestamp=datetime.now(timezone.utc)
        )
        create_error_event(db, event)
    
    count = get_project_error_count(db, test_project.id)
    assert count == 5
