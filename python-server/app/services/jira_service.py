import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import requests
from app.core.config import settings
from app.services.oauth_token_service import OAuthTokenService
from atlassian import Jira
from atlassian.errors import ApiError

logger = logging.getLogger(__name__)

# Atlassian API URLs
RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


class JiraService:
    """Service for interacting with Jira Cloud using Atlassian Python API"""

    def __init__(
        self,
        access_token: Optional[str] = None,
        user_id: Optional[str] = None,
        db_session: Optional[Any] = None,
    ):  # Modified to accept access_token
        self._client = None
        self._oauth2_token = None  # This will be set if access_token is provided
        self._token_service = None  # Original token service for non-user-specific calls
        self._cached_cloud_id = None
        self.user_id = user_id  # Store user_id if provided for multi-user context
        self.db_session = db_session  # Store db_session if provided

        if access_token:
            self._oauth2_token = {"access_token": access_token, "token_type": "Bearer"}
            # If an access_token is given, we might not need the full background service,
            # but we still need to initialize the client with this token.
            self._initialize_client_with_token(access_token)
        else:
            # Original initialization if no specific token is passed
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
                refresh_threshold=600,  # 10 minutes
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
                logger.info("Attempting to get cloud ID for OAuth2 initialization")
                cloud_id = self._get_cloud_id()
                logger.info(f"Result of cloud ID retrieval: {cloud_id}")

                if cloud_id:
                    # Using OAuth 2.0 with cloud ID
                    # Format the OAuth token according to the Atlassian Python API requirements
                    # The API expects an OAuth2 object with specific properties
                    oauth2_dict = {
                        "client_id": settings.JIRA_OAUTH_CLIENT_ID,
                        "token": {
                            "access_token": self._oauth2_token["access_token"],
                            "token_type": self._oauth2_token.get(
                                "token_type", "Bearer"
                            ),
                        },
                    }
                    url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
                    logger.info(f"Initializing Jira client with URL: {url}")
                    # Create custom headers for logging but don't pass to client init
                    headers = {
                        "Authorization": f"Bearer {self._oauth2_token['access_token']}",
                        "Accept": "application/json",
                    }
                    logger.info(f"Setting up authorization headers for API calls")

                    self._client = Jira(url=url, oauth2=oauth2_dict, cloud=True)
                    logger.info(
                        f"Jira client initialized with OAuth 2.0 for cloud ID: {cloud_id}"
                    )
                else:
                    logger.error(
                        "Could not obtain Jira Cloud ID. OAuth client initialization failed."
                    )

            # Otherwise, use basic authentication with API token
            elif (
                settings.JIRA_URL and settings.JIRA_USERNAME and settings.JIRA_API_TOKEN
            ):
                self._client = Jira(
                    url=settings.JIRA_URL,
                    username=settings.JIRA_USERNAME,
                    password=settings.JIRA_API_TOKEN,
                    cloud=True,
                )
                logger.info("Jira client initialized with API Token")

            else:
                logger.warning(
                    "No valid Jira credentials provided. Jira client not initialized."
                )

        except Exception as e:
            logger.error(f"Error initializing Jira client: {str(e)}")
            self._client = None

    def _initialize_client_with_token(self, access_token: str) -> None:
        """Initialize the Jira client using a provided OAuth2 access token."""
        try:
            logger.info(
                f"Initializing Jira client with provided access token for user: {self.user_id or 'unknown'}"
            )
            cloud_id = self._get_cloud_id(
                access_token_override=access_token
            )  # Pass token to _get_cloud_id

            if cloud_id:
                oauth2_dict = {
                    "client_id": settings.JIRA_OAUTH_CLIENT_ID,  # Still need client_id for context
                    "token": {"access_token": access_token, "token_type": "Bearer"},
                }
                url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
                self._client = Jira(url=url, oauth2=oauth2_dict, cloud=True)
                logger.info(
                    f"Jira client initialized with provided OAuth 2.0 token for cloud ID: {cloud_id}"
                )
            else:
                logger.error(
                    f"Could not obtain Jira Cloud ID with provided token. Client initialization failed for user: {self.user_id or 'unknown'}."
                )
        except Exception as e:
            logger.error(
                f"Error initializing Jira client with provided token for user {self.user_id or 'unknown'}: {str(e)}"
            )
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
        # Try direct API call if OAuth token is available, regardless of client initialization
        if self._oauth2_token and "access_token" in self._oauth2_token:
            try:
                logger.info("Testing Jira connection with direct API call")

                # Only log the first 10 characters to avoid security issues
                token_preview = self._oauth2_token["access_token"][:10] + "..."
                logger.info(f"Using OAuth token: {token_preview}")
                # Try to call the myself endpoint
                headers = {
                    "Authorization": f"Bearer {self._oauth2_token['access_token']}",
                    "Accept": "application/json",
                }
                cloud_id = self._cached_cloud_id or self._get_cloud_id()

                if cloud_id:
                    # First try the resources endpoint which is always accessible with the token
                    logger.info("Testing with resources endpoint first")
                    resources_url = (
                        "https://api.atlassian.com/oauth/token/accessible-resources"
                    )
                    resources_response = requests.get(resources_url, headers=headers)

                    if resources_response.status_code == 200:
                        logger.info(f"Successfully accessed resources endpoint")

                        # Now try a Jira-specific endpoint with lower permission requirements
                        urls_to_try = [
                            f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/2/serverInfo",
                            f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/serverInfo",
                            f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/2/myself",
                            f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself",
                        ]

                        for url in urls_to_try:
                            logger.info(f"Making direct API call to {url}")
                            response = requests.get(url, headers=headers)

                            if response.status_code == 200:
                                user_data = response.json()
                                logger.info(f"Connection test successful using {url}")
                                return True
                            else:
                                logger.warning(
                                    f"API endpoint {url} failed: {response.status_code} - {response.text}"
                                )

                        # If none of the specific endpoints work but resources endpoint does,
                        # assume we're connected but with limited permissions
                        logger.info(
                            "Connected to Atlassian API but may have limited Jira permissions"
                        )
                        return True
                    else:
                        logger.error(
                            f"Resources endpoint test failed: {resources_response.status_code} - {resources_response.text}"
                        )
                        return False
                else:
                    logger.error("Could not obtain cloud ID for connection test")
                    return False
            except Exception as e:
                logger.error(f"Direct API connection test failed: {str(e)}")
                if hasattr(e, "response") and hasattr(e.response, "text"):
                    logger.error(f"Response details: {e.response.text}")
                # Fall back to client method if available

        # Fall back to client method if available
        if not self._client:
            logger.warning("Jira client is not initialized and direct API call failed")
            return False

        try:
            # Print some debug info
            logger.info(
                f"Testing Jira connection using client: {self._client.__class__.__name__}"
            )
            if hasattr(self._client, "_options") and hasattr(
                self._client._options, "headers"
            ):
                auth_header = self._client._options.headers.get("Authorization", "None")
                if auth_header:
                    # Only log the first 10 characters to avoid security issues
                    logger.info(
                        f"Authorization header starts with: {auth_header[:10]}..."
                    )

            # Try to get current user to test connection
            result = self._client.myself()
            logger.info(
                f"Connection test successful: {result.get('displayName', 'Unknown user')}"
            )
            return True
        except Exception as e:
            logger.error(f"Jira connection test failed: {str(e)}")
            # Add more detailed error info
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Response details: {e.response.text}")
            return False

    def search_issues(
        self, jql: str, max_results: int = 20, fields: List[str] = None
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
            result = self._client.jql(jql, fields=fields, limit=max_results)

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
        additional_fields: Optional[Dict[str, Any]] = None,
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
            The created issue data"""
        if not self._client:
            raise ValueError("Jira client is not initialized")

        try:
            # Build the fields dictionary for issue creation
            fields = {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }

            # Add assignee if provided
            if assignee:
                fields["assignee"] = {"name": assignee}

            # Add components if provided
            if components:
                fields["components"] = [{"name": comp} for comp in components]

            # Add any additional fields
            if additional_fields:
                fields.update(additional_fields)

            # Create the issue using the correct API format
            result = self._client.create_issue(fields=fields)

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

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
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
            result = self._client.update_issue(issue_key=issue_key, fields=fields)

            return result
        except Exception as e:
            logger.error(f"Error updating Jira issue {issue_key}: {str(e)}")
            raise

    def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
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
            result = self._client.add_comment(issue_key=issue_key, comment=comment)

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
        # Use direct API call if OAuth token is available, regardless of client initialization
        if self._oauth2_token and "access_token" in self._oauth2_token:
            try:
                logger.info("Using direct API call for get_projects() with OAuth token")
                headers = {
                    "Authorization": f"Bearer {self._oauth2_token['access_token']}",
                    "Accept": "application/json",
                }
                cloud_id = self._cached_cloud_id or self._get_cloud_id()

                if cloud_id:
                    # Try different API versions and endpoints
                    urls_to_try = [
                        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/2/project",
                        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project",
                        # Add a query parameter that might be required
                        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/2/project?expand=description",
                        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project?expand=description",
                    ]

                    for url in urls_to_try:
                        try:
                            logger.info(f"Making direct API call to {url}")
                            response = requests.get(url, headers=headers)

                            if response.status_code == 200:
                                logger.info(
                                    f"Successfully retrieved projects from {url}"
                                )
                                return response.json()
                            else:
                                logger.warning(
                                    f"Failed to access {url}: {response.status_code} - {response.text}"
                                )
                        except Exception as e:
                            logger.warning(f"Error trying {url}: {str(e)}")

                    # If all attempts fail, raise the most informative error
                    logger.error("All project API endpoints failed")
                    raise ValueError(
                        "Could not retrieve Jira projects. API access denied."
                    )
                else:
                    logger.error("Could not obtain cloud ID for direct API call")
            except Exception as e:
                logger.warning(f"Direct API call failed: {str(e)}")
                # Continue to try client method if available

        # Fall back to client method if available
        if not self._client:
            raise ValueError(
                "Jira client is not initialized and direct API call failed"
            )

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
            logger.error(
                f"Error getting transitions for Jira issue {issue_key}: {str(e)}"
            )
            raise

    def transition_issue(
        self, issue_key: str, transition_id: str, comment: Optional[str] = None
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
                issue_key=issue_key, transition_id=transition_id, comment=comment
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
        # Use direct API call if OAuth token is available, regardless of client initialization
        if self._oauth2_token and "access_token" in self._oauth2_token:
            try:
                logger.info("Using direct API call for myself() with OAuth token")
                headers = {
                    "Authorization": f"Bearer {self._oauth2_token['access_token']}",
                    "Accept": "application/json",
                }
                cloud_id = self._cached_cloud_id or self._get_cloud_id()

                if cloud_id:
                    # Try v2 API endpoint first which might have different scope requirements
                    url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/2/myself"

                    logger.info(f"Making direct API call to {url}")
                    response = requests.get(url, headers=headers)

                    if response.status_code != 200:
                        # If v2 fails, try the v3 endpoint
                        url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself"
                        logger.info(f"V2 API failed, trying V3 API: {url}")
                        response = requests.get(url, headers=headers)

                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.error(
                            f"Direct API call failed: {response.status_code} - {response.text}"
                        )
                        # Try the user endpoint which might have different permissions
                        url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/user/search?query=currentUser"
                        logger.info(f"Trying alternative user endpoint: {url}")
                        response = requests.get(url, headers=headers)

                        if response.status_code == 200:
                            user_list = response.json()
                            if user_list and len(user_list) > 0:
                                return user_list[0]

                    # If all direct API calls fail, raise the error
                    response.raise_for_status()
                else:
                    logger.error("Could not obtain cloud ID for direct API call")
            except Exception as e:
                logger.warning(f"Direct API call failed: {str(e)}")
                # Continue to try client method if available

        # Fall back to client method if available
        if not self._client:
            raise ValueError(
                "Jira client is not initialized and direct API call failed"
            )

        try:
            result = self._client.myself()
            return result
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise

    def get_cloud_id(self) -> str:
        """
        Get the current cloud ID used by this service instance

        Returns:
            The current cloud ID or None if not available
        """
        if self._cached_cloud_id:
            return self._cached_cloud_id

        # Try to get it if not cached
        return self._get_cloud_id()

    def _get_cloud_id(
        self, access_token_override: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the Jira Cloud ID.
        Uses the instance's _oauth2_token by default, or access_token_override if provided.
        """
        if self._cached_cloud_id:
            return self._cached_cloud_id

        token_to_use = None
        if access_token_override:
            token_to_use = access_token_override
        elif self._oauth2_token and "access_token" in self._oauth2_token:
            token_to_use = self._oauth2_token["access_token"]

        if not token_to_use:
            logger.warning("No access token available to fetch cloud ID.")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {token_to_use}",
                "Accept": "application/json",
            }
            response = requests.get(RESOURCES_URL, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resources = response.json()
            if resources and isinstance(resources, list) and len(resources) > 0:
                # Assuming the first resource is the correct one
                self._cached_cloud_id = resources[0]["id"]
                logger.info(f"Retrieved cloud ID: {self._cached_cloud_id}")
                return self._cached_cloud_id
            else:
                logger.warning(
                    f"No accessible resources found or unexpected format: {resources}"
                )
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching accessible resources: {str(e)}")
            if e.response is not None:
                logger.error(
                    f"Response status: {e.response.status_code}, body: {e.response.text}"
                )
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching cloud ID: {str(e)}")
            return None

    def get_current_user_details(
        self, access_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for the current authenticated user using /rest/api/3/myself.
        If access_token is provided, it uses that token for the request.
        Otherwise, it uses the client initialized with the service-level token.
        """
        logger.info(
            f"Attempting to fetch current user details. Provided token: {'Yes' if access_token else 'No'}"
        )

        client_to_use = self._client
        token_for_direct_call = None

        if access_token:
            # If a specific access token is provided, we might need to make a direct request
            # or re-initialize a temporary client if the main one is for a different context.
            # For simplicity, let's try a direct request first.
            token_for_direct_call = access_token
            logger.info(
                f"Using provided access token for get_current_user_details for user: {self.user_id or 'profiling call'}"
            )
        elif self._oauth2_token and "access_token" in self._oauth2_token:
            token_for_direct_call = self._oauth2_token["access_token"]
            logger.info(
                f"Using service-level access token for get_current_user_details."
            )

        if token_for_direct_call:
            try:
                cloud_id = self._get_cloud_id(
                    access_token_override=token_for_direct_call
                )
                if not cloud_id:
                    logger.error("Cannot get user details: Cloud ID not found.")
                    return None

                myself_url = (
                    f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself"
                )
                headers = {
                    "Authorization": f"Bearer {token_for_direct_call}",
                    "Accept": "application/json",
                }
                response = requests.get(myself_url, headers=headers)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                user_details = response.json()
                logger.info(
                    f"Successfully fetched user details via direct call: {user_details.get('displayName')}"
                )
                return user_details
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Error fetching user details via direct API call: {str(e)}"
                )
                if e.response is not None:
                    logger.error(
                        f"Response status: {e.response.status_code}, body: {e.response.text}"
                    )
                # Fallback to client method if it exists and might be configured differently
                if (
                    client_to_use and not access_token
                ):  # Only fallback if not using a specific token
                    logger.info("Falling back to client.myself() method")
                else:
                    return None  # If specific token failed, don't use potentially wrong client
            except Exception as e:
                logger.error(
                    f"Unexpected error during direct API call for user details: {str(e)}"
                )
                return None

        # Fallback or default path: use the initialized client
        if not client_to_use:
            logger.warning("Jira client not initialized. Cannot fetch user details.")
            # If an access_token was provided but client init failed, this is the end of the road.
            if access_token:
                logger.error(
                    "Client initialization with provided access_token failed earlier."
                )
                return None
            # If no access_token was provided and client is None, it means service-level init failed.
            # Attempt to re-initialize the main client if it's not a user-specific call.
            logger.warning("Attempting to re-initialize service-level Jira client.")
            self._initialize_client()  # Try to re-init the main client
            client_to_use = self._client
            if not client_to_use:
                logger.error("Re-initialization of service-level Jira client failed.")
                return None

        try:
            logger.info(
                f"Using Jira client instance to call myself() for user: {self.user_id or 'service-level'}"
            )
            user_details = client_to_use.myself()
            logger.info(
                f"Successfully fetched user details via client.myself(): {user_details.get('displayName')}"
            )
            return user_details
        except ApiError as e:
            logger.error(
                f"Jira API Error fetching user details with client.myself(): {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Generic error fetching user details with client.myself(): {str(e)}"
            )
            return None


# Create a singleton instance
jira_service = JiraService()

# Ensure token service is stopped on application shutdown
import atexit

atexit.register(jira_service.stop_token_service)
