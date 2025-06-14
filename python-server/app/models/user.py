"""
Database models for users in the Jira Chatbot API.

This module defines the User model for tracking user data and authentication.
"""

import uuid

from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func


def generate_uuid():
    """Generate a random UUID string"""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication and user management"""

    __tablename__ = "users"

    # Primary key - UUID
    id = Column(String, primary_key=True, index=True, default=generate_uuid)

    # User identifiers
    email = Column(String, unique=True, index=True, nullable=True)
    jira_account_id = Column(String, index=True, nullable=True)
    username = Column(String, index=True, nullable=True)

    # User metadata
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Status flags
    is_active = Column(Boolean, default=True)

    # "Remember Me" feature preferences
    remember_me_enabled = Column(Boolean, default=False)
    extended_session_duration_days = Column(
        Integer, default=7
    )  # Default 7 days for "Remember Me"
    last_remember_me_login = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        """String representation of user"""
        return f"<User {self.email or self.jira_account_id or self.id}>"
