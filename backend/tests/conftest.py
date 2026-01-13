"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ["ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["JWT_EXPIRATION_DAYS"] = "30"

from app.database.database import Base, get_db
from app.main import app
from app.database import models


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = models.User(
        github_id="12345",
        username="testuser",
        email="test@example.com",
        name="Test User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_project(db, test_user):
    """Create a test project."""
    project = models.Project(
        project_key="test-project",
        name="Test Project",
        user_id=test_user.id,
        language="python",
        framework="fastapi"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def auth_token(test_user):
    """Generate a JWT token for test user."""
    from app.utils.auth import create_access_token
    return create_access_token(test_user.id, test_user.github_id)
