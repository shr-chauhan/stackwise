"""
Authentication utilities for JWT token validation
"""
import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db, models
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()

# Optional security scheme (doesn't raise error if token missing)
optional_security = HTTPBearer(auto_error=False)

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "30"))  # Default 30 days


def create_access_token(user_id: int, github_id: str) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: Database user ID
        github_id: GitHub user ID
    
    Returns:
        Encoded JWT token string
    """
    expiration = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "github_id": github_id,
        "exp": expiration,
        "iat": datetime.utcnow(),  # Issued at
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dict if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Usage:
        @app.get("/api/v1/projects")
        async def get_projects(current_user: User = Depends(get_current_user)):
            ...
    """
    try:
        token = credentials.credentials
        logger.debug(f"Authenticating with JWT token: {token[:20]}...")
        
        # Decode JWT token
        payload = decode_access_token(token)
        if not payload:
            logger.warning("Invalid or expired JWT token")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired API token"
            )
        
        # Get user ID from token payload
        user_id = int(payload.get("sub"))
        if not user_id:
            logger.warning("JWT token missing user ID")
            raise HTTPException(
                status_code=401,
                detail="Invalid token format"
            )
        
        # Fetch user from database
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            logger.warning(f"User not found for ID: {user_id}")
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error parsing user ID from token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token format"
        )
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
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        if not payload:
            return None
        
        user_id = int(payload.get("sub"))
        if not user_id:
            return None
        
        return db.query(models.User).filter(models.User.id == user_id).first()
    except Exception:
        return None

