"""
Jira User Lookup Service for mapping display names to account IDs.

This service provides functionality to:
1. Search for Jira users by display name
2. Cache user data locally for performance
3. Map display names to accountIds for assignee fields
4. Sync individual users on demand
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.models.user import User
from app.services.jira_service import JiraService
from app.services.jira_user_sync_service import JiraUserSyncService
from sqlalchemy import or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class JiraUserLookupService:
    """Service for looking up Jira users and mapping display names to account IDs"""

    def __init__(self, db_session: Session):
        """Initialize the user lookup service"""
        self.db_session = db_session
        self.sync_service = JiraUserSyncService(db_session)

    def get_accountid_for_assignee(
        self, assignee_name: str, jira_service: JiraService
    ) -> Optional[str]:
        """
        Get the accountId for an assignee name.
        This is the main method used by the issue creation/assignment logic.

        Args:
            assignee_name: Display name to look up (e.g., "Anson Chan")
            jira_service: Jira service instance

        Returns:
            accountId string or None if not found
        """
        try:
            # First, check local database cache
            cached_user = self._find_cached_user(assignee_name)
            if cached_user:
                logger.info(
                    f"Found cached user for assignee '{assignee_name}': {cached_user.jira_account_id}"
                )
                return (
                    str(cached_user.jira_account_id)
                    if cached_user.jira_account_id
                    else None
                )

            # If not cached, try to sync this specific user
            logger.info(
                f"User '{assignee_name}' not in cache, attempting to sync from Jira..."
            )
            sync_result = self.sync_service.sync_single_user_by_display_name(
                assignee_name, jira_service
            )

            if sync_result["success"]:
                account_id = sync_result.get("account_id")
                logger.info(f"Successfully synced user '{assignee_name}': {account_id}")
                return account_id
            else:
                logger.warning(
                    f"Failed to sync user '{assignee_name}': {sync_result.get('error')}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Error getting accountId for assignee '{assignee_name}': {str(e)}"
            )
            return None

    def _find_cached_user(self, display_name: str) -> Optional[User]:
        """Find user in local database cache"""
        try:
            # Search by display name (case-insensitive, exact match first)
            user = (
                self.db_session.query(User)
                .filter(User.display_name.ilike(display_name))
                .filter(User.jira_account_id.isnot(None))
                .filter(User.is_active.is_(True))
                .first()
            )

            if user:
                return user

            # Try partial match if exact match fails
            user = (
                self.db_session.query(User)
                .filter(User.display_name.ilike(f"%{display_name}%"))
                .filter(User.jira_account_id.isnot(None))
                .filter(User.is_active.is_(True))
                .first()
            )

            return user

        except Exception as e:
            logger.error(f"Error searching cached users: {str(e)}")
            return None

    def find_user_by_display_name(
        self, display_name: str, jira_service: JiraService
    ) -> Optional[Dict[str, Any]]:
        """
        Find a user by display name, returning full user info.

        Args:
            display_name: The display name to search for (e.g., "Anson Chan")
            jira_service: Jira service instance for API calls

        Returns:
            Dictionary with user info including accountId, or None if not found
        """
        try:
            # First check cache
            cached_user = self._find_cached_user(display_name)
            if cached_user:
                return {
                    "accountId": cached_user.jira_account_id,
                    "displayName": cached_user.display_name,
                    "emailAddress": cached_user.email or "",
                    "active": cached_user.is_active,
                }

            # If not cached, sync from Jira
            sync_result = self.sync_service.sync_single_user_by_display_name(
                display_name, jira_service
            )

            if sync_result["success"]:
                user = sync_result.get("user")
                if user:
                    return {
                        "accountId": user.jira_account_id,
                        "displayName": user.display_name,
                        "emailAddress": user.email or "",
                        "active": user.is_active,
                    }

            return None

        except Exception as e:
            logger.error(
                f"Error finding user by display name '{display_name}': {str(e)}"
            )
            return None

    def get_cached_user_count(self) -> int:
        """Get the number of cached Jira users"""
        try:
            return (
                self.db_session.query(User)
                .filter(User.jira_account_id.isnot(None))
                .count()
            )
        except Exception as e:
            logger.error(f"Error getting cached user count: {str(e)}")
            return 0
