"""
Security utilities for JWT token creation and verification.
Used for authentication and user session management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
import logging

from app.config import settings


logger = logging.getLogger(__name__)


# ===== JWT TOKEN FUNCTIONS =====

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Dictionary to encode in token (e.g., {"sub": "user_id"})
        expires_delta: Token expiration time (default: 30 minutes)
    
    Returns:
        Encoded JWT token string
    
    Example:
        token = create_access_token({"sub": "123"})
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        logger.debug(f"Token created for user {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation failed: {e}")
        raise


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT access token.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException 401: Invalid or expired token
    
    Example:
        payload = verify_access_token("eyJhbGc...")
        user_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        logger.debug(f"Token verified for user {payload.get('sub')}")
        return payload
    
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ===== OPTIONAL: PASSWORD HASHING (for future use) =====

from passlib.context import CryptContext

# Only needed if you implement username/password login
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
