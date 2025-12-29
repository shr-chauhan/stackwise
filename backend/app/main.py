import logging
import os
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db, engine, models
from app.schemas import schemas
from app.utils.crud import (
    create_error_event,
    get_error_event_by_id,
    get_error_events,
    get_error_analysis_by_event_id,
    get_error_analyses
)
from app.celery import analyze_error_event

# Configure logging
logger = logging.getLogger(__name__)

# Create tables only in development
if os.getenv("ENV", "development") == "development":
    from app.database.database import Base
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="Error Ingestion API", version="1.0.0")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/events", response_model=schemas.EventResponse)
async def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new error event.
    """
    try:
        db_event = create_error_event(db, event)
        
        # Enqueue AI analysis task if status_code >= 500 (non-blocking)
        if db_event.status_code and db_event.status_code >= 400:
            try:
                print(f"Enqueuing AI analysis task for error_event {db_event.id}")
                analyze_error_event.delay(db_event.id)
                logger.info(f"Enqueued AI analysis task for error_event {db_event.id}")
            except Exception as e:
                # Log but don't fail the request if task enqueueing fails
                logger.warning(f"Failed to enqueue AI analysis task: {e}")
        
        return schemas.EventResponse(
            id=db_event.id,
            timestamp=db_event.timestamp,
            message=event.message
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to ingest error event")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/v1/events", response_model=schemas.ErrorEventListResponse)
async def list_error_events(
    project_key: Optional[str] = Query(None, description="Filter by project key"),
    status_code: Optional[int] = Query(None, description="Filter by exact status code"),
    min_status_code: Optional[int] = Query(None, description="Filter by minimum status code"),
    max_status_code: Optional[int] = Query(None, description="Filter by maximum status code"),
    start_date: Optional[str] = Query(None, description="Filter events from this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter events until this date (ISO format)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: Session = Depends(get_db)
):
    """
    List error events with optional filtering and pagination.
    
    Supports filtering by:
    - project_key: Filter by specific project
    - status_code: Exact status code match
    - min_status_code / max_status_code: Range filtering
    - start_date / end_date: Date range filtering (ISO format)
    - limit / offset: Pagination
    """
    try:
        # Parse date strings if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if start_date.endswith('Z'):
                    start_date = start_date.replace('Z', '+00:00')
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}. Use ISO format.")
        
        if end_date:
            try:
                if end_date.endswith('Z'):
                    end_date = end_date.replace('Z', '+00:00')
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}. Use ISO format.")
        
        # Get error events
        events, total = get_error_events(
            db=db,
            project_key=project_key,
            status_code=status_code,
            min_status_code=min_status_code,
            max_status_code=max_status_code,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        event_items = []
        for event in events:
            # Check if analysis exists
            has_analysis = event.analysis is not None
            
            event_items.append(schemas.ErrorEventListItem(
                id=event.id,
                timestamp=event.timestamp,
                status_code=event.status_code,
                message=event.payload.get("message", ""),
                method=event.payload.get("method", ""),
                path=event.payload.get("path", ""),
                project_key=event.project.project_key,
                project_name=event.project.name,
                created_at=event.created_at,
                has_analysis=has_analysis
            ))
        
        return schemas.ErrorEventListResponse(
            events=event_items,
            total=total,
            limit=limit,
            offset=offset
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch error events")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v1/events/{event_id}", response_model=schemas.ErrorEventDetail)
async def get_error_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific error event by ID.
    """
    event = get_error_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Error event {event_id} not found")
    
    return schemas.ErrorEventDetail(
        id=event.id,
        timestamp=event.timestamp,
        status_code=event.status_code,
        payload=event.payload,
        created_at=event.created_at,
        project=schemas.ProjectInfo(
            id=event.project.id,
            project_key=event.project.project_key,
            name=event.project.name
        )
    )


@app.get("/api/v1/events/{event_id}/analysis", response_model=schemas.ErrorAnalysisResponse)
async def get_error_analysis(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Get AI analysis for a specific error event.
    """
    # Verify event exists
    event = get_error_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Error event {event_id} not found")
    
    # Get analysis
    analysis = get_error_analysis_by_event_id(db, event_id)
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis not found for error event {event_id}. Analysis may still be in progress."
        )
    
    return schemas.ErrorAnalysisResponse(
        id=analysis.id,
        error_event_id=analysis.error_event_id,
        analysis_text=analysis.analysis_text,
        model=analysis.model,
        confidence=analysis.confidence,
        created_at=analysis.created_at
    )


@app.get("/api/v1/events/{event_id}/with-analysis", response_model=schemas.ErrorEventWithAnalysis)
async def get_error_event_with_analysis(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an error event along with its analysis (if available).
    """
    # Get event
    event = get_error_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Error event {event_id} not found")
    
    # Get analysis (may be None)
    analysis = get_error_analysis_by_event_id(db, event_id)
    
    return schemas.ErrorEventWithAnalysis(
        event=schemas.ErrorEventDetail(
            id=event.id,
            timestamp=event.timestamp,
            status_code=event.status_code,
            payload=event.payload,
            created_at=event.created_at,
            project=schemas.ProjectInfo(
                id=event.project.id,
                project_key=event.project.project_key,
                name=event.project.name
            )
        ),
        analysis=schemas.ErrorAnalysisResponse(
            id=analysis.id,
            error_event_id=analysis.error_event_id,
            analysis_text=analysis.analysis_text,
            model=analysis.model,
            confidence=analysis.confidence,
            created_at=analysis.created_at
        ) if analysis else None
    )


@app.get("/api/v1/analysis", response_model=List[schemas.ErrorAnalysisResponse])
async def list_error_analyses(
    project_key: Optional[str] = Query(None, description="Filter by project key"),
    model: Optional[str] = Query(None, description="Filter by AI model name"),
    confidence: Optional[str] = Query(None, description="Filter by confidence level"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of analyses to return"),
    offset: int = Query(0, ge=0, description="Number of analyses to skip"),
    db: Session = Depends(get_db)
):
    """
    List error analyses with optional filtering and pagination.
    
    Supports filtering by:
    - project_key: Filter by specific project
    - model: Filter by AI model name (e.g., "gpt-4o-mini")
    - confidence: Filter by confidence level (e.g., "high", "medium", "low")
    - limit / offset: Pagination
    """
    try:
        analyses, total = get_error_analyses(
            db=db,
            project_key=project_key,
            model=model,
            confidence=confidence,
            limit=limit,
            offset=offset
        )
        
        return [
            schemas.ErrorAnalysisResponse(
                id=analysis.id,
                error_event_id=analysis.error_event_id,
                analysis_text=analysis.analysis_text,
                model=analysis.model,
                confidence=analysis.confidence,
                created_at=analysis.created_at
            )
            for analysis in analyses
        ]
    except Exception as e:
        logger.exception("Failed to fetch error analyses")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

