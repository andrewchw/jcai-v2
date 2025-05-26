"""
Pydantic schemas for the Jira Chatbot API.

These schemas define the request and response models for the API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# User schemas
class UserBase(BaseModel):
    """Base schema for user data"""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    jira_account_id: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""

    # At least one identifier must be provided
    pass


class UserResponse(UserBase):
    """Schema for user response"""

    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Token schemas
class TokenResponse(BaseModel):
    """Schema for token response"""

    status: str  # "active", "expired", "error"
    expires_in_seconds: Optional[int] = None
    expires_at: Optional[str] = None
    provider: str = "jira"
    last_used: Optional[str] = None

    class Config:
        from_attributes = True


# OAuth schemas
class OAuthRequest(BaseModel):
    """Schema for OAuth request"""

    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    jira_account_id: Optional[str] = None


class OAuthResponse(BaseModel):
    """Schema for OAuth response"""

    success: bool
    message: str
    redirect_url: Optional[str] = None


# Project and issue schemas (same as existing ones)
class Project(BaseModel):
    """Schema for Jira project"""

    id: str
    key: str
    name: str


class Issue(BaseModel):
    """Schema for Jira issue"""

    key: str
    summary: str
    status: str
    assignee: Optional[str] = None
    updated: Optional[str] = None


# Chat schemas
class ChatMessage(BaseModel):
    """Schema for incoming chat message"""

    text: str
    timestamp: Optional[datetime] = None


class ChatResponse(BaseModel):
    """Schema for chat response following Dialogflow pattern"""

    text: str
    intent: str
    entities: Dict[str, Any] = {}
    confidence: float
    requires_clarification: bool = False
    jira_action_result: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
