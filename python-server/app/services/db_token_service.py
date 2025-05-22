"""
Multi-user token service for Jira Chatbot API.

Extends the original token service to support multiple users with database storage.
"""

from sqlalchemy.orm import Session
from app.models.token import OAuthToken
from app.models.user import User
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

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
    
    def store_token(self, user_id: str, token_data: Dict[str, Any], provider: str = "jira") -> OAuthToken:
        """
        Save a token for a user.
        
        Args:
            user_id: The user ID
            token_data: Dictionary with token data
            provider: The token provider (default: jira)
            
        Returns:
            The saved token
        """
        # Check if token exists
        token = self.get_token(user_id, provider)
        
        if token:
            # Update existing token
            token.access_token = token_data.get("access_token")
            
            if refresh_token := token_data.get("refresh_token"):
                token.refresh_token = refresh_token
                
            token.expires_at = token_data.get("expires_at")
            token.token_type = token_data.get("token_type", "Bearer")
            token.last_refreshed_at = datetime.now().timestamp()
            
            # Copy any additional data
            additional_data = {k: v for k, v in token_data.items() if k not in 
                             ["access_token", "refresh_token", "token_type", "expires_at"]}
            if additional_data:
                token.additional_data = additional_data
                
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
        return self.db.query(OAuthToken).filter(OAuthToken.is_active == True).all()
    
    def update_last_used(self, user_id: str, provider: str = "jira") -> bool:
        """Update the last used timestamp for a token"""
        token = self.get_token(user_id, provider)
        if not token:
            return False
        
        token.last_used_at = datetime.now().timestamp()
        self.db.commit()
        return True
    
    def token_to_dict(self, token: OAuthToken) -> Dict[str, Any]:
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
            **(token.additional_data or {})
        }
