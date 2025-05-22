from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from app.services.jira_service import JiraService
from app.models.token import OAuthToken
from app.core.database import get_db # FastAPI dependency for DB session

# Use APIRouter for FastAPI
user_profile_router = APIRouter(
    prefix='/user',
    tags=["user"]
)

logger = logging.getLogger(__name__)

def get_token_data_for_user(user_id: str, db: Session) -> dict | None:
    logger.info(f"Attempting to retrieve token for user_id: {user_id}")
    token_data = None
    try:
        user_token_entry = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
        
        if user_token_entry:
            token_data = {
                "access_token": user_token_entry.access_token,
                "refresh_token": user_token_entry.refresh_token,
                "expires_at": user_token_entry.expires_at,
            }
            if user_token_entry.access_token:
                logger.info(f"Token successfully retrieved and decrypted for user_id {user_id} via direct model query.")
            else:
                logger.warning(f"Token entry found for user_id {user_id}, but decrypted access_token is None.")
                token_data = None
        else:
            logger.warning(f"No OAuthToken entry found for user_id {user_id} in the database.")
    except Exception as e:
        logger.exception(f"Error querying/processing OAuthToken for user_id {user_id}: {e}")
        return None
            
    return token_data

@user_profile_router.get('/profile')
async def get_user_profile(user_id: str = Query(...), db: Session = Depends(get_db)):
    if not user_id:
        # Query(...) should make this check redundant, but as a safeguard:
        logger.warning("User profile request somehow bypassed user_id requirement")
        raise HTTPException(status_code=400, detail="user_id parameter is required")

    logger.info(f"Attempting to fetch user profile for user_id: {user_id}")

    try:
        token_data = get_token_data_for_user(user_id, db)

        if not token_data or not token_data.get('access_token'):
            logger.warning(f"No valid access token could be retrieved for user_id: {user_id}. Token data: {token_data}")
            raise HTTPException(status_code=401, detail="User not authenticated or access token not found")

        access_token = token_data['access_token']
            
        logger.info(f"Valid access token retrieved for user_id: {user_id}")

        # Initialize JiraService with the user's access_token.
        jira_client = JiraService(access_token=access_token, user_id=user_id, db_session=db)
        
        user_details = jira_client.get_current_user_details(access_token=access_token)

        if user_details and user_details.get('displayName'):
            response_data = {
                "displayName": user_details.get("displayName"),
                "accountId": user_details.get("accountId"),
                "emailAddress": user_details.get("emailAddress"),
                "avatarUrls": user_details.get("avatarUrls")
            }
            logger.info(f"Successfully fetched profile for user_id {user_id}: {response_data.get('displayName')}")
            return response_data
        else:
            error_message = "Failed to retrieve user details from Jira or displayName missing."
            logger.warning(f"{error_message} Jira response: {str(user_details)[:200]} for user_id: {user_id}")
            raise HTTPException(status_code=500, detail=error_message)

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.exception(f"Exception in get_user_profile for user_id {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

# The APIRouter instance (user_profile_router) will be imported and included 
# in app/api/routes.py or app/main.py
