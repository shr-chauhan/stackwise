from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Tuple
from datetime import datetime
from app.database import models
from app.schemas import schemas


def get_or_create_project(db: Session, project_key: str, project_name: str = None):
    """Get existing project or create new one (thread-safe)"""
    project = db.query(models.Project).filter_by(project_key=project_key).first()
    
    if project:
        return project
    
    try:
        project = models.Project(
            project_key=project_key,
            name=project_name or project_key
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    except IntegrityError:
        # Race condition: another request created the project between our check and insert
        db.rollback()
        return db.query(models.Project).filter_by(project_key=project_key).one()


def create_error_event(db: Session, event: schemas.EventCreate):
    """Create a new error event"""
    # Get or create project
    project = get_or_create_project(db, event.project_key)
    
    # Create payload (status_code is now stored as a column, not in payload)
    payload = {
        "message": event.message,
        "stack": event.stack,
        "method": event.method,
        "path": event.path,
    }
    
    # Create error event
    # timestamp is already a datetime object from Pydantic validation
    # created_at will be set automatically by the database
    db_event = models.ErrorEvent(
        timestamp=event.timestamp,
        project_id=project.id,
        status_code=event.status_code,
        payload=payload
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event


def get_error_event_by_id(db: Session, event_id: int) -> Optional[models.ErrorEvent]:
    """Get a single error event by ID"""
    return db.query(models.ErrorEvent).filter(models.ErrorEvent.id == event_id).first()


def get_error_events(
    db: Session,
    project_key: Optional[str] = None,
    status_code: Optional[int] = None,
    min_status_code: Optional[int] = None,
    max_status_code: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[models.ErrorEvent], int]:
    """
    Get error events with filtering and pagination.
    
    Returns:
        Tuple of (list of error events, total count)
    """
    query = db.query(models.ErrorEvent).join(models.Project)
    
    # Apply filters
    if project_key:
        query = query.filter(models.Project.project_key == project_key)
    
    if status_code is not None:
        query = query.filter(models.ErrorEvent.status_code == status_code)
    else:
        if min_status_code is not None:
            query = query.filter(models.ErrorEvent.status_code >= min_status_code)
        if max_status_code is not None:
            query = query.filter(models.ErrorEvent.status_code <= max_status_code)
    
    if start_date:
        query = query.filter(models.ErrorEvent.timestamp >= start_date)
    
    if end_date:
        query = query.filter(models.ErrorEvent.timestamp <= end_date)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering
    events = query.order_by(models.ErrorEvent.timestamp.desc()).offset(offset).limit(limit).all()
    
    return events, total


def get_error_analysis_by_event_id(
    db: Session,
    error_event_id: int
) -> Optional[models.ErrorAnalysis]:
    """Get error analysis for a specific error event"""
    return db.query(models.ErrorAnalysis).filter(
        models.ErrorAnalysis.error_event_id == error_event_id
    ).first()


def get_error_analyses(
    db: Session,
    project_key: Optional[str] = None,
    model: Optional[str] = None,
    confidence: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[models.ErrorAnalysis], int]:
    """
    Get error analyses with filtering and pagination.
    
    Returns:
        Tuple of (list of error analyses, total count)
    """
    query = db.query(models.ErrorAnalysis).join(
        models.ErrorEvent
    ).join(models.Project)
    
    # Apply filters
    if project_key:
        query = query.filter(models.Project.project_key == project_key)
    
    if model:
        query = query.filter(models.ErrorAnalysis.model == model)
    
    if confidence:
        query = query.filter(models.ErrorAnalysis.confidence == confidence)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering
    analyses = query.order_by(models.ErrorAnalysis.created_at.desc()).offset(offset).limit(limit).all()
    
    return analyses, total

