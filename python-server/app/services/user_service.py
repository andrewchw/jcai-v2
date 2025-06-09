"""
User service for Jira Chatbot API.

This module provides functions for managing users in the database.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.user import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users in the database"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_jira_account_id(self, jira_account_id: str) -> Optional[User]:
        """Get a user by Jira account ID"""
        return (
            self.db.query(User).filter(User.jira_account_id == jira_account_id).first()
        )

    def get_or_create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Get an existing user or create a new one.

        Args:
            user_data: Dictionary with user data (email, jira_account_id, id, etc.)

        Returns:
            User object
        """
        # Try to find existing user by identifiers
        user = None

        # First try to find by ID if provided
        if user_id := user_data.get("id"):
            user = self.get_by_id(user_id)

        if not user and (email := user_data.get("email")):
            user = self.get_by_email(email)

        if not user and (jira_id := user_data.get("jira_account_id")):
            user = self.get_by_jira_account_id(jira_id)

        # If user exists, update fields and return
        if user:
            # Update any changed fields
            for key, value in user_data.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            # Update last login time
            user.last_login = datetime.now()  # type: ignore

            self.db.commit()
            return user

        # Create new user
        user = User(**user_data)
        user.last_login = datetime.now()  # type: ignore

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Created new user: {user.id}")
        return user

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()

    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
        """Update user data"""
        user = self.get_by_id(user_id)
        if not user:
            return None

        for key, value in user_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: str) -> bool:
        """Delete a user by ID"""
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True
