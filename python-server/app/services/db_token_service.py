"""
Multi-user token service for Jira Chatbot API.

Extends the original token service to support multiple users with database storage.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.token import OAuthToken
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DBTokenService:
    """Service for managing OAuth tokens in the database"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    def get_token(self, user_id: str, provider: str = "jira") -> Optional[OAuthToken]:
        """Get a token by user ID and provider"""
        token_id = f"{user_id}:{provider}"
        return self.db.query(OAuthToken).filter(OAuthToken.id == token_id).first()

    def store_token(
        self, user_id: str, token_data: Dict[str, Any], provider: str = "jira"
    ) -> Optional[OAuthToken]:
        """
        Save a token for a user.

        Args:
            user_id: The user ID
            token_data: Dictionary with token data
            provider: The token provider (default: jira)

        Returns:
            The saved token
        """  # Check if token exists
        token = self.get_token(user_id, provider)

        if token:
            # Update existing token
            token.access_token = token_data.get("access_token")
            if refresh_token := token_data.get("refresh_token"):
                token.refresh_token = refresh_token

            token.expires_at = token_data.get("expires_at")  # type: ignore
            token.token_type = token_data.get("token_type", "Bearer")
            token.last_refreshed_at = datetime.now().timestamp()  # type: ignore

            # Copy any additional data
            additional_data = {
                k: v
                for k, v in token_data.items()
                if k
                not in ["access_token", "refresh_token", "token_type", "expires_at"]
            }
            if additional_data:
                token.additional_data = additional_data  # type: ignore
        else:
            # Create new token
            token = OAuthToken.from_dict(user_id, token_data, provider)
            self.db.add(token)

        self.db.commit()
        self.db.refresh(token)

        return token

    def delete_token(self, user_id: str, provider: str = "jira") -> bool:
        """Delete a token by user ID and provider"""
        token = self.get_token(user_id, provider)
        if not token:
            return False

        self.db.delete(token)
        self.db.commit()
        return True

    def list_active_tokens(self) -> List[OAuthToken]:
        """List all active tokens"""
        return self.db.query(OAuthToken).filter(OAuthToken.is_active.is_(True)).all()

    def update_last_used(self, user_id: str, provider: str = "jira") -> bool:
        """Update the last used timestamp for a token"""
        token = self.get_token(user_id, provider)
        if not token:
            return False

        token.last_used_at = datetime.now().timestamp()  # type: ignore
        self.db.commit()
        return True

    def token_to_dict(self, token: OAuthToken) -> Optional[Dict[str, Any]]:
        """Convert a token to a dictionary format"""
        if not token:
            return None

        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "token_type": token.token_type,
            "expires_at": token.expires_at,
            "created_at": token.created_at,
            "scope": token.scope,
            **(token.additional_data or {}),  # type: ignore
        }

    def enable_extended_session(
        self, user_id: str, provider: str = "jira", extended_duration_days: int = 7
    ) -> bool:
        """Enable extended session for "Remember Me" functionality"""
        token = self.get_token(user_id, provider)
        if not token:
            return False

        token.enable_extended_session(extended_duration_days)
        self.db.commit()
        logger.info(
            f"Extended session enabled for user {user_id} with {extended_duration_days} days duration"
        )
        return True

    def disable_extended_session(self, user_id: str, provider: str = "jira") -> bool:
        """Disable extended session and revert to original expiration"""
        token = self.get_token(user_id, provider)
        if not token:
            return False

        token.disable_extended_session()
        self.db.commit()
        logger.info(f"Extended session disabled for user {user_id}")
        return True

    def is_extended_session_enabled(self, user_id: str, provider: str = "jira") -> bool:
        """Check if extended session is enabled for a user"""
        token = self.get_token(user_id, provider)
        return token.is_extended_session if token else False

    def get_tokens_needing_refresh(
        self, refresh_threshold_seconds: int = 600
    ) -> List[OAuthToken]:
        """Get all tokens that need refreshing within the threshold"""
        current_time = datetime.now().timestamp()
        threshold_time = current_time + refresh_threshold_seconds

        # Query for active tokens that will expire within the threshold
        tokens = (
            self.db.query(OAuthToken)
            .filter(
                OAuthToken.is_active.is_(True),
                OAuthToken.refresh_token_encrypted.isnot(
                    None
                ),  # Must have refresh token
            )
            .all()
        )

        # Filter by effective expiration time (considering extended sessions)
        tokens_needing_refresh = []
        for token in tokens:
            if token.effective_expires_at <= threshold_time:
                tokens_needing_refresh.append(token)

        return tokens_needing_refresh

    def get_expired_tokens(self) -> List[OAuthToken]:
        """Get all expired tokens"""
        current_time = datetime.now().timestamp()

        tokens = self.db.query(OAuthToken).filter(OAuthToken.is_active.is_(True)).all()

        expired_tokens = []
        for token in tokens:
            if token.effective_expires_at <= current_time:
                expired_tokens.append(token)

        return expired_tokens

    def mark_token_inactive(self, user_id: str, provider: str = "jira") -> bool:
        """Mark a token as inactive (soft delete)"""
        token = self.get_token(user_id, provider)
        if not token:
            return False

        token.is_active = False
        self.db.commit()
        logger.info(f"Token marked as inactive for user {user_id}")
        return True

    def get_all_active_users(self, provider: str = "jira") -> List[str]:
        """Get all user IDs with active tokens"""
        tokens = (
            self.db.query(OAuthToken)
            .filter(OAuthToken.is_active.is_(True), OAuthToken.provider == provider)
            .all()
        )

        return [token.user_id for token in tokens]

    def update_token_from_refresh(
        self, user_id: str, token_data: Dict[str, Any], provider: str = "jira"
    ) -> Optional[OAuthToken]:
        """Update token with refreshed data while preserving extended session settings"""
        token = self.get_token(user_id, provider)
        if not token:
            return None

        # Update token data
        token.access_token = token_data.get("access_token")
        if refresh_token := token_data.get("refresh_token"):
            token.refresh_token = refresh_token

        # Handle expiration based on session type
        new_expires_at = token_data.get("expires_at")
        if not new_expires_at and "expires_in" in token_data:
            expires_in = token_data.get("expires_in", 3600)
            new_expires_at = datetime.now().timestamp() + expires_in

        if token.is_extended_session:
            # For extended sessions, update the base expiration but keep extended expiration
            token.expires_at = new_expires_at
            # Don't update extended_expires_at - it should remain as set
        else:
            # For regular sessions, just update normal expiration
            token.expires_at = new_expires_at

        token.token_type = token_data.get("token_type", "Bearer")
        token.last_refreshed_at = datetime.now().timestamp()

        # Copy any additional data
        additional_data = {
            k: v
            for k, v in token_data.items()
            if k
            not in [
                "access_token",
                "refresh_token",
                "token_type",
                "expires_at",
                "expires_in",
            ]
        }
        if additional_data:
            token.additional_data = additional_data

        self.db.commit()
        self.db.refresh(token)

        logger.info(
            f"Token refreshed for user {user_id} (extended_session: {token.is_extended_session})"
        )
        return token
