"""
Database configuration module for the Jira Chatbot API.

Provides SQLAlchemy database setup and utilities for managing database connections.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Determine database URL - default to SQLite for development
DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{Path(__file__).parent.parent.parent}/data/tokens.db"
)

# Create data directory if using SQLite
if DATABASE_URL.startswith("sqlite"):
    db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
    db_dir = db_path.parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)

# Create SQLAlchemy engine with proper settings for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
    echo=os.environ.get("SQL_ECHO", "false").lower()
    == "true",  # SQL echoing for debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
Base = declarative_base()


# Database dependency for FastAPI
def get_db():
    """
    Dependency function to get database session.
    Use this as a FastAPI dependency to get a database session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
