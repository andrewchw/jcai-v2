"""
Debug endpoints to help troubleshoot OAuth2 and Jira API issues.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.services.multi_user_jira_service import MultiUserJiraService
from app.services.db_token_service import DBTokenService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["debug"],
    responses={404: {"description": "Not found"}},
)

@router.get("/oauth-config")
async def get_oauth_config():
    """
    Get the current OAuth2 configuration.
    
    Returns:
        Dictionary with OAuth2 configuration values
    """
    return {
        "client_id": settings.JIRA_OAUTH_CLIENT_ID,
        "callback_url": settings.JIRA_OAUTH_CALLBACK_URL,
        "cloud_id": settings.ATLASSIAN_OAUTH_CLOUD_ID,
    }

@router.get("/user-token-info")
async def get_user_token_info(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get information about a user's token.
    
    Args:
        user_id: The user ID to get token information for
    
    Returns:
        Dictionary with token information
    """
    try:
        # Get token info
        token_service = DBTokenService(db)
        token = token_service.get_token(user_id)
        
        if not token:
            raise HTTPException(
                status_code=404,
                detail="No token found for this user"
            )
        
        # Convert to dict for display (hide sensitive parts)
        token_dict = token_service.token_to_dict(token)
        
        # Create a sanitized version for display
        sanitized_token = {
            "access_token": token_dict.get("access_token", "")[:10] + "..." if token_dict.get("access_token") else None,
            "refresh_token": token_dict.get("refresh_token", "")[:10] + "..." if token_dict.get("refresh_token") else None,
            "expires_at": token_dict.get("expires_at"),
            "token_type": token_dict.get("token_type"),
            "scope": token_dict.get("scope"),
        }
        
        # Try to get Jira service and cloud ID
        multi_service = MultiUserJiraService(db)
        jira_service = multi_service.get_jira_service(user_id)
        
        cloud_id = None
        is_connected = False
        
        if jira_service:
            cloud_id = jira_service.get_cloud_id()
            is_connected = jira_service.is_connected()
        
        return {
            "user_id": user_id,
            "token": sanitized_token,
            "cloud_id": cloud_id,
            "is_connected": is_connected,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting token info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get token info: {str(e)}"
        )
