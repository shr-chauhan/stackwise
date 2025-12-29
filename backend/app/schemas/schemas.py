from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


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
                return datetime.utcnow()
        return datetime.utcnow()


class EventResponse(BaseModel):
    id: int
    timestamp: datetime
    message: str

    class Config:
        from_attributes = True


# Response schemas for fetching errors
class ProjectInfo(BaseModel):
    id: int
    project_key: str
    name: str

    class Config:
        from_attributes = True


class ErrorEventDetail(BaseModel):
    id: int
    timestamp: datetime
    status_code: Optional[int]
    payload: Dict[str, Any]
    created_at: datetime
    project: ProjectInfo

    class Config:
        from_attributes = True


class ErrorEventListItem(BaseModel):
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

    class Config:
        from_attributes = True


class ErrorEventListResponse(BaseModel):
    events: List[ErrorEventListItem]
    total: int
    limit: int
    offset: int


class ErrorAnalysisResponse(BaseModel):
    id: int
    error_event_id: int
    analysis_text: str
    model: str
    confidence: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorEventWithAnalysis(BaseModel):
    event: ErrorEventDetail
    analysis: Optional[ErrorAnalysisResponse] = None

