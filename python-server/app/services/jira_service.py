from typing import Dict, Any, List, Optional, Union
import logging
import json
import os
import requests
from atlassian import Jira
from atlassian.errors import ApiError

from app.core.config import settings
from app.services.oauth_token_service import OAuthTokenService

logger = logging.getLogger(__name__)

# Atlassian API URLs
RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"

class JiraService:
    """Service for interacting with Jira Cloud using Atlassian Python API"""
    
    def __init__(self):
        self._client = None
        self._oauth2_token = None
        self._token_service = None
        self._cached_cloud_id = None
        self._initialize_token_service()
        self._initialize_client()
    
    def _initialize_token_service(self) -> None:
        """Initialize the OAuth token service for background refresh"""
        if settings.JIRA_OAUTH_CLIENT_ID and settings.JIRA_OAUTH_CLIENT_SECRET:
            token_file = os.getenv("TOKEN_FILE", "oauth_token.json")
            token_url = "https://auth.atlassian.com/oauth/token"
            
            # Create and start token service
            self._token_service = OAuthTokenService(
                client_id=settings.JIRA_OAUTH_CLIENT_ID,
                client_secret=settings.JIRA_OAUTH_CLIENT_SECRET,
                token_url=token_url,
                token_file=token_file,
                check_interval=300,  # 5 minutes
                refresh_threshold=600  # 10 minutes
            )
            
            # Add an event handler to log token events
            self._token_service.add_event_handler(self._handle_token_event)
            
            # Start the background refresh process
            self._token_service.start()
            logger.info("OAuth token background refresh service started")
            
            # Load the current token if available
            token = self._token_service.load_token()
            if token:
                self._oauth2_token = token
    
    def _handle_token_event(self, event):
        """Handle token refresh events"""
        if event.event_type == "refresh":
            logger.info(f"Token refresh event: {event.message}")
            # Update the client with the refreshed token
            self._oauth2_token = self._token_service.load_token()
            self._initialize_client()
        elif event.event_type == "error":
            logger.error(f"Token error event: {event.message}")
        else:
            logger.info(f"Token event ({event.event_type}): {event.message}")
      
    def _initialize_client(self) -> None:
        """Initialize the Jira client using configuration settings"""
        try:
            # Check if we have OAuth2 credentials
            if settings.JIRA_OAUTH_CLIENT_ID and self._oauth2_token:
                # Using OAuth 2.0
                # First, get the cloud ID by calling the resources endpoint
                cloud_id = self._get_cloud_id()
                
                if cloud_id:
                    # Using OAuth 2.0 with cloud ID
                    oauth2_dict = {
                        "client_id": settings.JIRA_OAUTH_CLIENT_ID,
                        "token": {
                            "access_token": self._oauth2_token["access_token"],
                            "token_type": "Bearer"
                        }
                    }
                    self._client = Jira(
                        url=f"https://api.atlassian.com/ex/jira/{cloud_id}",
                        oauth2=oauth2_dict,
                        cloud=True
                    )
                    logger.info(f"Jira client initialized with OAuth 2.0 for cloud ID: {cloud_id}")
            
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
        
        # Save the token using the token service
        if self._token_service:
            self._token_service.save_token(token)
        
        # Completely reset client to clear any cached information
        self._client = None
        self._cached_cloud_id = None
        
        # Reinitialize the client with the new token
        self._initialize_client()
    
    def get_oauth2_token(self) -> Dict[str, Any]:
        """
        Get the current OAuth2 token, refreshing if needed via token service
        
        Returns:
            The current OAuth2 token
        """
        if self._token_service:
            # Let the token service handle refreshing if needed
            token = self._token_service.load_token()
            if token != self._oauth2_token:
                self._oauth2_token = token
                self._initialize_client()
            return token
        
        return self._oauth2_token
    
    def refresh_oauth2_token(self, force: bool = False) -> Dict[str, Any]:
        """
        Force refresh the OAuth2 token
        
        Args:
            force: Force refresh even if not expired
        
        Returns:
            The refreshed OAuth2 token
        """
        if self._token_service and self._oauth2_token:
            # Use token service to refresh the token
            token = self._token_service.refresh_token(self._oauth2_token, force)
            if token:
                self._oauth2_token = token
                self._initialize_client()
            return token
        
        return self._oauth2_token
    
    def stop_token_service(self) -> None:
        """Stop the background token refresh service"""
        if self._token_service:
            self._token_service.stop()
            logger.info("OAuth token background refresh service stopped")
    
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
            # If fields parameter is None, set default fields
            if not fields:
                # Convert default fields to comma-separated string if needed
                fields = "summary,status,assignee,priority,duedate,created,updated"
            elif isinstance(fields, list):
                # Convert list of fields to comma-separated string
                fields = ",".join(fields)
                
            # Use jql method for JQL queries
            result = self._client.jql(
                jql,
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
    
    def _get_cloud_id(self) -> Optional[str]:
        """
        Get the Jira Cloud ID using the access token
        
        Returns:
            Cloud ID string or None if not available
        """
        # Return cached cloud ID if available
        if self._cached_cloud_id:
            logger.debug(f"Using cached cloud ID: {self._cached_cloud_id}")
            return self._cached_cloud_id
            
        if not self._oauth2_token or "access_token" not in self._oauth2_token:
            logger.warning("No OAuth token available for cloud ID retrieval")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self._oauth2_token['access_token']}",
                "Accept": "application/json"
            }
            
            logger.info("Retrieving Jira Cloud ID from accessible resources...")
            response = requests.get(RESOURCES_URL, headers=headers)
            response.raise_for_status()
            resources = response.json()
            
            if not resources:
                logger.warning("No accessible Jira resources found")
                return None
            
            # Use the first cloud ID (most common scenario)
            self._cached_cloud_id = resources[0]["id"]
            site_name = resources[0].get("name", "Unknown Site")
            logger.info(f"Found Jira Cloud site: {site_name} (ID: {self._cached_cloud_id})")
            return self._cached_cloud_id
            
        except Exception as e:
            logger.error(f"Error retrieving Jira Cloud ID: {str(e)}")
            return None
    
    def reset_client(self) -> None:
        """
        Reset the Jira client and all cached information
        Use this when changing authentication methods or when connection issues occur
        """
        self._client = None
        self._cached_cloud_id = None
        logger.info("Jira client has been reset")
        # Reinitialize with current settings
        self._initialize_client()


# Create a singleton instance
jira_service = JiraService()

# Ensure token service is stopped on application shutdown
import atexit
atexit.register(jira_service.stop_token_service)
