from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class EventCreate(BaseModel):
    project_key: str = Field(..., description="Project key identifier")
    message: str = Field(..., description="Error message")
    stack: Optional[str] = Field(None, description="Error stack trace")
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="Request path")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    timestamp: datetime = Field(..., description="ISO timestamp")
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        """Parse timestamp string to datetime, with fallback to current time if invalid"""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                # Handle ISO format with 'Z' timezone
                if v.endswith('Z'):
                    v = v.replace('Z', '+00:00')
                return datetime.fromisoformat(v)
            except (ValueError, AttributeError):
                # Fallback to current time if parsing fails
                return datetime.now(timezone.utc)
        return datetime.now(timezone.utc)


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime
    message: str


# Response schemas for fetching errors
class ProjectInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_key: str
    name: str


class ErrorEventDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime
    status_code: Optional[int]
    payload: Dict[str, Any]
    created_at: datetime
    project: ProjectInfo


class ErrorEventListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime
    status_code: Optional[int]
    message: str
    method: str
    path: str
    project_key: str
    project_name: str
    created_at: datetime
    has_analysis: bool = False


class ErrorEventListResponse(BaseModel):
    events: List[ErrorEventListItem]
    total: int
    limit: int
    offset: int


class ErrorAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    error_event_id: int
    analysis_text: str
    model: str
    confidence: Optional[str]
    has_source_code: bool  # True if source code was used in analysis, False if only stack trace
    created_at: datetime


class ErrorEventWithAnalysis(BaseModel):
    event: ErrorEventDetail
    analysis: Optional[ErrorAnalysisResponse] = None


# Project management schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    project_key: str = Field(..., description="Project key (unique identifier)")
    language: Optional[str] = Field(None, description="Primary programming language (e.g., python, javascript, typescript)")
    framework: Optional[str] = Field(None, description="Framework used (e.g., django, react, express, spring)")
    description: Optional[str] = Field(None, description="Project description and context")
    repo_provider: Optional[str] = Field("github", description="Repository provider (github, gitlab)")
    repo_owner: Optional[str] = Field(None, description="Repository owner/username")
    repo_name: Optional[str] = Field(None, description="Repository name")
    branch: Optional[str] = Field("main", description="Repository branch")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    language: Optional[str] = Field(None, description="Primary programming language (e.g., python, javascript, typescript)")
    framework: Optional[str] = Field(None, description="Framework used (e.g., django, react, express, spring)")
    description: Optional[str] = Field(None, description="Project description and context")
    repo_provider: Optional[str] = Field(None, description="Repository provider (github, gitlab)")
    repo_owner: Optional[str] = Field(None, description="Repository owner/username")
    repo_name: Optional[str] = Field(None, description="Repository name")
    branch: Optional[str] = Field(None, description="Repository branch")


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_key: str
    name: str
    language: Optional[str] = None
    framework: Optional[str] = None
    description: Optional[str] = None
    repo_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    error_count: Optional[int] = 0  # Will be populated by query


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


# User management schemas
class UserSyncRequest(BaseModel):
    github_id: str = Field(..., description="GitHub user ID")
    username: str = Field(..., description="GitHub username")
    email: Optional[str] = Field(None, description="GitHub email")
    name: Optional[str] = Field(None, description="GitHub display name")
    avatar_url: Optional[str] = Field(None, description="GitHub avatar URL")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    github_id: str
    username: str
    email: Optional[str]
    name: Optional[str]
    avatar_url: Optional[str]
    api_token: str
    created_at: datetime

