from typing import Dict, Any, List, Optional, Union
import logging
import json
from atlassian import Jira
from atlassian.errors import ApiError

from app.core.config import settings

logger = logging.getLogger(__name__)

class JiraService:
    """Service for interacting with Jira Cloud using Atlassian Python API"""
    
    def __init__(self):
        self._client = None
        self._oauth2_token = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Jira client using configuration settings"""
        try:
            # Check if we have OAuth2 credentials
            if settings.JIRA_OAUTH_CLIENT_ID and self._oauth2_token:
                # Using OAuth 2.0
                oauth2_dict = {
                    "client_id": settings.JIRA_OAUTH_CLIENT_ID,
                    "token": self._oauth2_token
                }
                self._client = Jira(
                    url=settings.JIRA_URL,
                    oauth2=oauth2_dict,
                    cloud=True
                )
                logger.info("Jira client initialized with OAuth 2.0")
            
            # Otherwise, use basic authentication with API token
            elif settings.JIRA_URL and settings.JIRA_USERNAME and settings.JIRA_API_TOKEN:
                self._client = Jira(
                    url=settings.JIRA_URL,
                    username=settings.JIRA_USERNAME,
                    password=settings.JIRA_API_TOKEN,
                    cloud=True
                )
                logger.info("Jira client initialized with API Token")
            
            else:
                logger.warning("No valid Jira credentials provided. Jira client not initialized.")
        
        except Exception as e:
            logger.error(f"Error initializing Jira client: {str(e)}")
            self._client = None
    
    def set_oauth2_token(self, token: Dict[str, str]) -> None:
        """
        Set the OAuth2 token and reinitialize the client
        
        Args:
            token: OAuth 2.0 token dictionary containing at least access_token and token_type
        """
        self._oauth2_token = token
        self._initialize_client()
    
    def is_connected(self) -> bool:
        """Check if the Jira client is connected and working"""
        if not self._client:
            return False
        
        try:
            # Try to get current user to test connection
            self._client.myself()
            return True
        except Exception as e:
            logger.error(f"Jira connection test failed: {str(e)}")
            return False

    def search_issues(
        self,
        jql: str,
        max_results: int = 20,
        fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Search for Jira issues using JQL
        
        Args:
            jql: The JQL query string
            max_results: Maximum number of results to return
            fields: List of fields to include in the results
            
        Returns:
            The issues found by the search
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            if not fields:
                fields = "summary,status,assignee,priority,duedate,created,updated"
            
            # For Cloud instances, use enhanced_jql for better performance
            result = self._client.enhanced_jql(
                jql_str=jql,
                fields=fields,
                limit=max_results
            )
            
            return result
        except Exception as e:
            logger.error(f"Error searching Jira issues: {str(e)}")
            raise
    
    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
        assignee: Optional[str] = None,
        components: Optional[List[str]] = None,
        additional_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Jira issue
        
        Args:
            project_key: The project key (e.g., "PROJ")
            summary: Issue summary
            description: Issue description
            issue_type: Issue type (e.g., "Task", "Bug")
            assignee: Assignee's email or username
            components: List of component names
            additional_fields: Dictionary of additional fields
            
        Returns:
            The created issue data
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            # Prepare components string if provided
            components_str = None
            if components:
                components_str = ",".join(components)
            
            # Create the issue
            result = self._client.create_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                assignee=assignee,
                components=components_str,
                additional_fields=additional_fields or {}
            )
            
            return result
        except Exception as e:
            logger.error(f"Error creating Jira issue: {str(e)}")
            raise
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get a Jira issue by key
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            
        Returns:
            The issue data
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            result = self._client.get_issue(issue_key)
            return result
        except Exception as e:
            logger.error(f"Error getting Jira issue {issue_key}: {str(e)}")
            raise
    
    def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a Jira issue
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            fields: Dictionary of fields to update
            
        Returns:
            The updated issue data
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            result = self._client.update_issue(
                issue_key=issue_key,
                fields=fields
            )
            
            return result
        except Exception as e:
            logger.error(f"Error updating Jira issue {issue_key}: {str(e)}")
            raise
    
    def add_comment(
        self,
        issue_key: str,
        comment: str
    ) -> Dict[str, Any]:
        """
        Add a comment to a Jira issue
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            comment: Comment text
            
        Returns:
            The added comment data
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            result = self._client.add_comment(
                issue_key=issue_key,
                comment=comment
            )
            
            return result
        except Exception as e:
            logger.error(f"Error adding comment to Jira issue {issue_key}: {str(e)}")
            raise
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all Jira projects
        
        Returns:
            List of projects
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            result = self._client.projects()
            return result
        except Exception as e:
            logger.error(f"Error getting Jira projects: {str(e)}")
            raise
    
    def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get available transitions for a Jira issue
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            
        Returns:
            List of available transitions
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            result = self._client.get_transitions(issue_key)
            return result
        except Exception as e:
            logger.error(f"Error getting transitions for Jira issue {issue_key}: {str(e)}")
            raise
    
    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transition a Jira issue to a new status
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            transition_id: ID of the transition
            comment: Optional comment for the transition
            
        Returns:
            The updated issue data
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            result = self._client.transition_issue(
                issue_key=issue_key,
                transition_id=transition_id,
                comment=comment
            )
            
            return result
        except Exception as e:
            logger.error(f"Error transitioning Jira issue {issue_key}: {str(e)}")
            raise
    
    def myself(self) -> Dict[str, Any]:
        """
        Get information about the current user
        
        Returns:
            Current user data
        """
        if not self._client:
            raise ValueError("Jira client is not initialized")
        
        try:
            result = self._client.myself()
            return result
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise


# Create a singleton instance
jira_service = JiraService()
