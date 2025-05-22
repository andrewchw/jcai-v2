"""
Multi-user Jira service extension for Jira Chatbot API.

This module extends the regular JiraService to support multiple users.
"""

from sqlalchemy.orm import Session
from app.services.jira_service import JiraService
from app.services.user_service import UserService
from app.services.db_token_service import DBTokenService
from typing import Dict, Any, Optional
import logging

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
        """        # Remove existing service
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
