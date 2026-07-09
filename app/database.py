"""
Database configuration and session management.
Handles connection pooling, session creation, and database initialization.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from app.config import settings, SQLALCHEMY_KWARGS
from typing import Generator


# ===== DATABASE ENGINE SETUP =====

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    **SQLALCHEMY_KWARGS,
    # For local SQLite testing (optional):
    # connect_args={"check_same_thread": False},
    # poolclass=StaticPool,
)


# ===== SESSION FACTORY =====

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ===== BASE CLASS FOR MODELS =====

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    All model classes inherit from this.
    """
    pass


# ===== DATABASE DEPENDENCY =====

def get_db() -> Generator:
    """
    Dependency injection for database sessions.
    Used in FastAPI route handlers:
    
    @router.get("/items")
    def get_items(db: Session = Depends(get_db)):
        return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== DATABASE INITIALIZATION =====

def create_all_tables():
    """
    Create all database tables defined in models.
    Run this once during app startup or migration.
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """
    Drop all tables. Use with caution!
    """
    Base.metadata.drop_all(bind=engine)
