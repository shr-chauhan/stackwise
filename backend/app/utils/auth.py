"""
Authentication utilities for API token validation
"""
import secrets
import logging
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db, models

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()

# Optional security scheme (doesn't raise error if token missing)
optional_security = HTTPBearer(auto_error=False)


def generate_api_token() -> str:
    """Generate a secure random API token"""
    return f"da_{secrets.token_urlsafe(32)}"  # "da_" prefix for Debug AI


def get_user_by_token(db: Session, token: str) -> Optional[models.User]:
    """Get user by API token"""
    return db.query(models.User).filter(models.User.api_token == token).first()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get current authenticated user from API token.
    
    Usage:
        @app.get("/api/v1/projects")
        async def get_projects(current_user: User = Depends(get_current_user)):
            ...
    """
    try:
        token = credentials.credentials
        logger.debug(f"Authenticating with token: {token[:10]}...")
        
        user = get_user_by_token(db, token)
        if not user:
            logger.warning(f"Invalid token provided: {token[:10]}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired API token"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """
    Optional authentication - returns None if no token provided.
    Useful for endpoints that work with or without auth.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    return get_user_by_token(db, token)

