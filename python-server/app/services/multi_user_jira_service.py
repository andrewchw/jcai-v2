"""
Multi-user Jira service extension for Jira Chatbot API.

This module extends the regular JiraService to support multiple users.
"""

import logging
from typing import Any, Dict, Optional

from app.services.db_token_service import DBTokenService
from app.services.jira_service import JiraService
from app.services.user_service import UserService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MultiUserJiraService:
    """
    Service for managing Jira API interactions for multiple users.

    This service creates and manages JiraService instances for individual users.
    """

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.user_service = UserService(db)
        self.token_service = DBTokenService(db)
        self._jira_services = {}  # user_id -> JiraService

    def get_jira_service(self, user_id: str) -> Optional[JiraService]:
        """
        Get or create a JiraService instance for a user.

        Args:
            user_id: The user ID

        Returns:
            JiraService instance or None if token not found
        """
        # If we already have a service for this user, return it
        if user_id in self._jira_services:
            return self._jira_services[user_id]

        # Get the user's token
        token = self.token_service.get_token(user_id)
        if not token:
            logger.warning(f"No token found for user {user_id}")
            return None

        # Convert token to dict format
        token_dict = self.token_service.token_to_dict(token)

        # Create a new service
        service = JiraService()
        service.set_oauth2_token(token_dict)

        # Store service
        self._jira_services[user_id] = service

        return service

    def refresh_jira_service(self, user_id: str) -> Optional[JiraService]:
        """
        Refresh the JiraService for a user (recreate with fresh token).

        Args:
            user_id: The user ID

        Returns:
            JiraService instance or None if token not found
        """  # Remove existing service
        if user_id in self._jira_services:
            del self._jira_services[user_id]

        # Create new service
        return self.get_jira_service(user_id)

    def save_token_for_user(self, user_id: str, token_data: Dict[str, Any]) -> bool:
        """
        Save a token for a user.

        Args:
            user_id: The user ID
            token_data: Dictionary with token data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save token to DB
            self.token_service.store_token(user_id, token_data)

            # Refresh Jira service if it exists
            if user_id in self._jira_services:
                self.refresh_jira_service(user_id)

            return True
        except Exception as e:
            logger.error(f"Error saving token for user {user_id}: {str(e)}")
            return False

    def get_token_for_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get token for a user.

        Args:
            user_id: The user ID

        Returns:
            Token dictionary or None if not found
        """
        token = self.token_service.get_token(user_id)
        if not token:
            return None

        # Update last used timestamp
        self.token_service.update_last_used(user_id)

        # Return token dict
        return self.token_service.token_to_dict(token)

    def logout_user(self, user_id: str) -> bool:
        """
        Logout a user by removing their token.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        # Remove service if it exists
        if user_id in self._jira_services:
            del self._jira_services[user_id]

        # Delete token
        return self.token_service.delete_token(user_id)

    def get_or_create_user(self, user_data: Dict[str, Any]) -> str:
        """
        Get or create a user and return their ID.

        Args:
            user_data: Dictionary with user data

        Returns:
            User ID
        """
        user = self.user_service.get_or_create_user(user_data)
        return user.id

    # Jira Action Methods for Chat Integration

    async def create_issue(
        self, user_id: str, issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new Jira issue for a user.

        Args:
            user_id: The user ID
            issue_data: Dictionary with issue data

        Returns:
            Result dictionary with success status and data
        """
        try:
            jira_service = self.get_jira_service(user_id)
            if not jira_service:
                return {"success": False, "error": "User not authenticated"}

            # Extract fields from issue_data
            project_key = issue_data.get("project", {}).get("key", "JCAI")
            summary = issue_data.get("summary", "New task from chatbot")
            description = issue_data.get("description", "")
            issue_type = issue_data.get("issuetype", {}).get("name", "Task")

            # Optional fields
            assignee = None
            if "assignee" in issue_data:
                assignee = issue_data["assignee"].get("name")

            additional_fields = {}
            if "priority" in issue_data:
                additional_fields["priority"] = issue_data["priority"]

            # Create the issue using JiraService
            result = jira_service.create_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                assignee=assignee,
                additional_fields=additional_fields,
            )

            return {"success": True, "issue": result}

        except Exception as e:
            logger.error(f"Error creating issue for user {user_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def assign_issue(
        self, user_id: str, issue_key: str, assignee: str
    ) -> Dict[str, Any]:
        """
        Assign an issue to a user.

        Args:
            user_id: The user ID
            issue_key: Jira issue key
            assignee: Username to assign to

        Returns:
            Result dictionary with success status
        """
        try:
            jira_service = self.get_jira_service(user_id)
            if not jira_service:
                return {"success": False, "error": "User not authenticated"}

            # Update the issue with new assignee
            fields = {"assignee": {"name": assignee}}
            result = jira_service.update_issue(issue_key, fields)

            return {"success": True, "issue": result}

        except Exception as e:
            logger.error(
                f"Error assigning issue {issue_key} for user {user_id}: {str(e)}"
            )
            return {"success": False, "error": str(e)}

    async def transition_issue(
        self, user_id: str, issue_key: str, status: str
    ) -> Dict[str, Any]:
        """
        Transition an issue to a new status.

        Args:
            user_id: The user ID
            issue_key: Jira issue key
            status: Target status name

        Returns:
            Result dictionary with success status
        """
        try:
            jira_service = self.get_jira_service(user_id)
            if not jira_service:
                return {"success": False, "error": "User not authenticated"}

            # Get available transitions
            transitions = jira_service.get_transitions(issue_key)

            # Find matching transition
            transition_id = None
            for transition in transitions:
                if transition["to"]["name"].lower() == status.lower():
                    transition_id = transition["id"]
                    break

            if not transition_id:
                return {
                    "success": False,
                    "error": f"No transition available to status '{status}'",
                }

            # Execute transition
            result = jira_service.transition_issue(issue_key, transition_id)

            return {"success": True, "issue": result}

        except Exception as e:
            logger.error(
                f"Error transitioning issue {issue_key} for user {user_id}: {str(e)}"
            )
            return {"success": False, "error": str(e)}

    async def search_issues(
        self, user_id: str, jql: str, max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Search for issues using JQL.

        Args:
            user_id: The user ID
            jql: JQL query string
            max_results: Maximum number of results

        Returns:
            Result dictionary with success status and issues
        """
        try:
            jira_service = self.get_jira_service(user_id)
            if not jira_service:
                return {"success": False, "error": "User not authenticated"}

            # Search issues
            result = jira_service.search_issues(jql, max_results)

            return {"success": True, "issues": result.get("issues", [])}

        except Exception as e:
            logger.error(f"Error searching issues for user {user_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def add_comment(
        self, user_id: str, issue_key: str, comment: str
    ) -> Dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            user_id: The user ID
            issue_key: Jira issue key
            comment: Comment text

        Returns:
            Result dictionary with success status
        """
        try:
            jira_service = self.get_jira_service(user_id)
            if not jira_service:
                return {"success": False, "error": "User not authenticated"}

            # Add comment
            result = jira_service.add_comment(issue_key, comment)

            return {"success": True, "comment": result}

        except Exception as e:
            logger.error(
                f"Error adding comment to issue {issue_key} for user {user_id}: {str(e)}"
            )
            return {"success": False, "error": str(e)}
