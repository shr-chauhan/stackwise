from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(String, unique=True, index=True, nullable=False)  # GitHub user ID
    username = Column(String, nullable=False, index=True)  # GitHub username
    email = Column(String, nullable=True, index=True)  # GitHub email
    name = Column(String, nullable=True)  # GitHub display name
    avatar_url = Column(String, nullable=True)  # GitHub avatar URL
    api_token = Column(String, unique=True, index=True, nullable=False)  # API authentication token
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    # Repository configuration for AI debugging (stored as JSON)
    repo_config = Column(JSON, nullable=True)  # {owner, repo, branch, provider, access_token}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    error_events = relationship("ErrorEvent", back_populates="project")


class ErrorEvent(Base):
    __tablename__ = "error_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status_code = Column(Integer, nullable=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="error_events")
    analysis = relationship("ErrorAnalysis", back_populates="error_event", uselist=False)


class ErrorAnalysis(Base):
    __tablename__ = "error_analysis"

    id = Column(Integer, primary_key=True, index=True)
    error_event_id = Column(Integer, ForeignKey("error_events.id"), nullable=False, unique=True, index=True)
    analysis_text = Column(Text, nullable=False)  # Using Text for longer analysis content
    model = Column(String, nullable=False)  # e.g., "gpt-4", "claude-3", etc.
    confidence = Column(String, nullable=True)  # Store as string to allow flexible formats
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    error_event = relationship("ErrorEvent", back_populates="analysis")

