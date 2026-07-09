"""
Authentication routes for Google OAuth 2.0.
Handles user login, token generation, and JWT validation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from google.auth.transport import requests
from google.oauth2 import id_token
import logging
from typing import Optional

from app.config import settings, GOOGLE_OAUTH_CONFIG
from app.database import get_db
from app.models import User
from app.schemas import GoogleTokenRequest, TokenResponse, UserResponse
from app.utils.security import create_access_token, verify_access_token


logger = logging.getLogger(__name__)
router = APIRouter()


# ===== HELPER: Extract Token from Header =====

def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return parts[1]


# ===== DEPENDENCY: Get Current User =====

async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Usage in routes:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    payload = verify_access_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# ===== GOOGLE OAUTH LOGIN =====

@router.post("/google", response_model=TokenResponse)
async def google_login(request: GoogleTokenRequest, db: Session = Depends(get_db)):
    """
    Google OAuth 2.0 login endpoint.
    
    Frontend sends the Google OAuth ID token.
    Backend verifies it and creates a JWT token.
    
    Args:
        request: GoogleTokenRequest with 'token' (Google OAuth ID token)
        db: Database session
    
    Returns:
        TokenResponse with JWT token and user info
    
    Raises:
        HTTPException 401: Invalid or expired Google token
    """
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            request.token,
            requests.Request(),
            clock_skew_in_seconds=10
        )
        
        # Extract user info from token
        google_id = idinfo.get("sub")
        email = idinfo.get("email")
        name = idinfo.get("name")
        
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required fields",
            )
        
        # Check if user exists
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Create new user
            logger.info(f"Creating new user: {email}")
            user = User(
                google_id=google_id,
                email=email,
                name=name or email.split("@")[0],
                role="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update last login (optional)
            logger.info(f"User login: {email}")
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
    
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


# ===== GET CURRENT USER INFO =====

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    
    Headers:
        Authorization: Bearer <JWT token>
    
    Returns:
        UserResponse with user details
    """
    return UserResponse.model_validate(current_user)