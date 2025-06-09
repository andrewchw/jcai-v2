"""Database models for OAuth tokens in the Jira Chatbot API.

This module defines the Token model for storing and managing OAuth tokens.
"""

import os
from datetime import datetime

from app.core.database import Base
from cryptography.fernet import Fernet
from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, String
from sqlalchemy.orm import relationship

# Setup encryption for tokens
# In production, store this in a secure location outside of code
ENCRYPTION_KEY = os.environ.get("JIRA_TOKEN_ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    # Generate a key if not provided - should only happen in development
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    os.environ["JIRA_TOKEN_ENCRYPTION_KEY"] = ENCRYPTION_KEY

cipher_suite = Fernet(
    ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
)


class OAuthToken(Base):
    """OAuth token model for storing and managing OAuth tokens."""

    __tablename__ = "oauth_tokens"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # User relationship
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    user = relationship("User", backref="oauth_tokens")

    # Provider information
    provider = Column(
        String, index=True, default="jira"
    )  # e.g., "jira", "github", etc.

    # Token data (encrypted)
    access_token_encrypted = Column(String, nullable=False)
    refresh_token_encrypted = Column(String, nullable=True)
    token_type = Column(String, default="Bearer")

    # Token metadata
    expires_at = Column(Float, nullable=False)  # Unix timestamp
    created_at = Column(
        Float, nullable=False, default=lambda: datetime.now().timestamp()
    )
    last_used_at = Column(Float, nullable=True)
    last_refreshed_at = Column(Float, nullable=True)

    # "Remember Me" feature fields
    is_extended_session = Column(Boolean, default=False)
    extended_expires_at = Column(
        Float, nullable=True
    )  # Extended expiration for "Remember Me"
    original_expires_at = Column(Float, nullable=True)  # Original short-term expiration

    # Additional data
    scope = Column(String, nullable=True)
    additional_data = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        """Get string representation of token."""
        return f"<OAuthToken {self.id} for user {self.user_id} ({self.provider})>"

    @property
    def access_token(self):
        """Get decrypted access token."""
        if not self.access_token_encrypted:
            return None
        return cipher_suite.decrypt(self.access_token_encrypted.encode()).decode()

    @access_token.setter
    def access_token(self, value):
        """Set encrypted access token."""
        if value is None:
            self.access_token_encrypted = None
        else:
            self.access_token_encrypted = cipher_suite.encrypt(value.encode()).decode()

    @property
    def refresh_token(self):
        """Get decrypted refresh token."""
        if not self.refresh_token_encrypted:
            return None
        return cipher_suite.decrypt(self.refresh_token_encrypted.encode()).decode()

    @refresh_token.setter
    def refresh_token(self, value):
        """Set encrypted refresh token."""
        if value is None:
            self.refresh_token_encrypted = None
        else:
            self.refresh_token_encrypted = cipher_suite.encrypt(value.encode()).decode()

    @property
    def effective_expires_at(self):
        """Get the effective expiration time considering extended sessions."""
        if self.is_extended_session and self.extended_expires_at:
            return self.extended_expires_at
        return self.expires_at

    @property
    def is_expired(self):
        """Check if token is expired (considering extended sessions)."""
        return self.effective_expires_at < datetime.now().timestamp()

    @property
    def seconds_to_expiry(self):
        """Get seconds until token expires (considering extended sessions)."""
        return max(0, self.effective_expires_at - datetime.now().timestamp())

    def enable_extended_session(self, extended_duration_days=7):
        """Enable extended session for "Remember Me" functionality."""
        self.is_extended_session = True
        self.original_expires_at = self.expires_at
        self.extended_expires_at = datetime.now().timestamp() + (
            extended_duration_days * 24 * 60 * 60
        )

    def disable_extended_session(self):
        """Disable extended session and revert to original expiration."""
        self.is_extended_session = False
        if self.original_expires_at:
            self.expires_at = self.original_expires_at
        self.extended_expires_at = None
        self.original_expires_at = None

    def to_dict(self):
        """Convert token to dictionary format (for use with existing token-handling code)."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.effective_expires_at,  # Use effective expiration
            "created_at": self.created_at,
            "scope": self.scope,
            "is_extended_session": self.is_extended_session,
            "extended_expires_at": self.extended_expires_at,
            **(self.additional_data or {}),
        }

    @classmethod
    def from_dict(cls, user_id, token_dict, provider="jira"):
        """Create a token from dictionary data."""
        # Create copy to avoid modifying original
        token_data = token_dict.copy()

        # Extract required fields
        access_token = token_data.pop("access_token", None)
        refresh_token = token_data.pop("refresh_token", None)
        token_type = token_data.pop("token_type", "Bearer")
        expires_at = token_data.pop("expires_at", None)
        scope = token_data.pop("scope", None)

        # Extract extended session fields
        is_extended_session = token_data.pop("is_extended_session", False)
        extended_expires_at = token_data.pop("extended_expires_at", None)

        # If expires_at is not provided but expires_in is, calculate expires_at
        if expires_at is None and "expires_in" in token_data:
            expires_in = token_data.pop("expires_in", 3600)
            expires_at = datetime.now().timestamp() + expires_in

        # Create token instance
        token = cls(
            id=f"{user_id}:{provider}",
            user_id=user_id,
            provider=provider,
            token_type=token_type,
            expires_at=expires_at,
            scope=scope,
            is_extended_session=is_extended_session,
            extended_expires_at=extended_expires_at,
            additional_data=token_data,
        )

        # Set encrypted fields
        token.access_token = access_token
        token.refresh_token = refresh_token

        return token
