"""
Tests for main API endpoints.
"""
import pytest
from datetime import datetime, timezone
from fastapi import status


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_create_event_success(client, test_project):
    """Test creating an error event successfully."""
    event_data = {
        "project_key": "test-project",
        "message": "Test error message",
        "stack": "Error: Test\n  at test.js:1:1",
        "method": "GET",
        "path": "/test",
        "status_code": 500,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post("/api/v1/events", json=event_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert data["message"] == "Test error message"
    assert "timestamp" in data


def test_create_event_missing_project_key(client):
    """Test creating event with missing project_key."""
    event_data = {
        "message": "Test error",
        "method": "GET",
        "path": "/test",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post("/api/v1/events", json=event_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_event_invalid_project_key(client):
    """Test creating event with non-existent project_key."""
    event_data = {
        "project_key": "non-existent",
        "message": "Test error",
        "method": "GET",
        "path": "/test",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post("/api/v1/events", json=event_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not exist" in response.json()["detail"]


def test_list_events_requires_auth(client):
    """Test that listing events requires authentication."""
    response = client.get("/api/v1/events")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_events_success(client, test_user, test_project, auth_token, db):
    """Test listing events with authentication."""
    # Create a test event directly in the database
    from app.utils.crud import create_error_event
    from app.schemas.schemas import EventCreate
    
    event = EventCreate(
        project_key="test-project",
        message="Test error",
        method="GET",
        path="/test",
        status_code=500,
        timestamp=datetime.now(timezone.utc)
    )
    create_error_event(db, event)
    
    # List events
    response = client.get(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "events" in data
    assert "total" in data
    assert isinstance(data["events"], list)


def test_get_event_by_id_requires_auth(client, test_project):
    """Test that getting event by ID requires authentication."""
    response = client.get("/api/v1/events/1")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_event_by_id_not_found(client, auth_token):
    """Test getting non-existent event."""
    response = client.get(
        "/api/v1/events/99999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_sync_user_success(client, db):
    """Test user sync endpoint."""
    user_data = {
        "github_id": "67890",
        "username": "newuser",
        "email": "newuser@example.com",
        "name": "New User"
    }
    
    response = client.post("/api/v1/auth/sync-user", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["github_id"] == "67890"
    assert data["username"] == "newuser"
    assert "api_token" in data
    assert len(data["api_token"]) > 0


def test_sync_user_missing_github_id(client):
    """Test user sync with missing github_id."""
    user_data = {
        "username": "newuser"
    }
    
    response = client.post("/api/v1/auth/sync-user", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_sync_user_empty_github_id(client):
    """Test user sync with empty github_id."""
    user_data = {
        "github_id": "",
        "username": "newuser"
    }
    
    response = client.post("/api/v1/auth/sync-user", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_project_requires_auth(client):
    """Test that creating project requires authentication."""
    project_data = {
        "name": "New Project",
        "project_key": "new-project"
    }
    
    response = client.post("/api/v1/projects", json=project_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_project_success(client, auth_token):
    """Test creating a project successfully."""
    project_data = {
        "name": "New Project",
        "project_key": "new-project",
        "language": "python",
        "framework": "django"
    }
    
    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Project"
    assert data["project_key"] == "new-project"
    assert data["language"] == "python"
    assert "id" in data


def test_create_project_duplicate_key(client, test_project, auth_token):
    """Test creating project with duplicate key."""
    project_data = {
        "name": "Another Project",
        "project_key": "test-project"  # Already exists
    }
    
    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_list_projects_requires_auth(client):
    """Test that listing projects requires authentication."""
    response = client.get("/api/v1/projects")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_projects_success(client, test_project, auth_token):
    """Test listing projects."""
    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert len(data["projects"]) > 0
    assert data["projects"][0]["project_key"] == "test-project"
