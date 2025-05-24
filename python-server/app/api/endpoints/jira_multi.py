"""
Multi-user Jira API endpoints for Jira Chatbot API.

These endpoints provide Jira API access for multiple users.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.multi_user_jira_service import MultiUserJiraService
from app.schemas.api_schemas import Project, Issue
from typing import List, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jira/v2",
    tags=["jira-multiuser"],
    responses={404: {"description": "Not found"}},
)


@router.get("/projects", response_model=List[Project])
async def get_jira_projects(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a list of Jira projects for a specific user.
    
    Args:
        user_id: The ID of the user to get projects for
    """
    try:
        multi_service = MultiUserJiraService(db)
        jira_service = multi_service.get_jira_service(user_id)
        
        if not jira_service:
            raise HTTPException(
                status_code=401,
                detail="No authentication token found for this user"
            )
        
        if not jira_service.is_connected():
            raise HTTPException(
                status_code=500,
                detail="Not connected to Jira. Please check your OAuth token."
            )
        
        # Get projects using the token
        projects = jira_service.get_projects()
        
        # Convert to response model
        project_list = []
        for project in projects:
            project_list.append(Project(
                id=project["id"],
                key=project["key"],
                name=project["name"]
            ))
        
        return project_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Jira projects: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Jira projects: {str(e)}"
        )


@router.get("/issues", response_model=List[Issue])
async def get_jira_issues(
    user_id: str,
    project_key: Optional[str] = Query(None, description="Jira project key"),
    max_results: int = Query(10, description="Maximum number of issues to return"),
    jql: Optional[str] = Query(None, description="JQL query for filtering issues"),
    db: Session = Depends(get_db)
):
    """
    Get a list of Jira issues for a specific user.
    
    Args:
        user_id: The ID of the user to get issues for
        project_key: Optional Jira project key to filter issues
        max_results: Maximum number of issues to return
    """
    try:
        multi_service = MultiUserJiraService(db)
        jira_service = multi_service.get_jira_service(user_id)
        
        if not jira_service:
            raise HTTPException(
                status_code=401,
                detail="No authentication token found for this user"
            )
        
        if not jira_service.is_connected():
            raise HTTPException(
                status_code=500,
                detail="Not connected to Jira. Please check your OAuth token."
            )        # Build JQL query with proper search restrictions to avoid "Unbounded JQL" errors
        if jql:
            # Use the provided JQL query (already includes user filtering from frontend)
            final_jql = jql
            logger.info(f"Using provided JQL query: {final_jql}")
        elif project_key:
            # Fallback: construct user-focused query with project filter
            final_jql = f"project = {project_key} AND assignee = currentUser() AND updated >= -30d ORDER BY updated DESC"
            logger.info(f"Constructed project-specific JQL query: {final_jql}")        
        else:
            # Fallback: construct user-focused query for JCAI project by default
            final_jql = "project = JCAI AND assignee = currentUser() AND updated >= -30d ORDER BY updated DESC"
            logger.info(f"Constructed JCAI project default JQL query: {final_jql}")
        
        # Search for issues using the token
        result = jira_service.search_issues(jql=final_jql, max_results=max_results)
        
        # Extract issues from result
        issues = []
        for issue in result.get("issues", []):
            issues.append(Issue(
                key=issue["key"],
                summary=issue["fields"]["summary"],
                status=issue["fields"]["status"]["name"],
                assignee=issue["fields"]["assignee"]["displayName"] if issue["fields"].get("assignee") else None,
                updated=issue["fields"]["updated"]
            ))
        
        return issues
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Jira issues: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Jira issues: {str(e)}"
        )


@router.get("/user", response_model=dict)
async def get_jira_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get information about the current Jira user (myself).
    
    Args:
        user_id: The ID of the user to get information for
    """
    try:
        multi_service = MultiUserJiraService(db)
        jira_service = multi_service.get_jira_service(user_id)
        
        if not jira_service:
            raise HTTPException(
                status_code=401,
                detail="No authentication token found for this user"
            )
        if not jira_service.is_connected():
            raise HTTPException(
                status_code=500,
                detail="Not connected to Jira. Please check your OAuth token."
            )
        
        try:
            # Try to get user info using the jira_service.myself() method
            user_info = jira_service.myself()
            
            # If the method returns a value, return it
            return user_info
        except Exception as e:
            logger.warning(f"Cannot retrieve user info using myself(): {str(e)}")
            
            # If that fails, try to get basic user info from the OAuth token
            try:
                # Get the cloud ID
                cloud_id = jira_service.get_cloud_id()
                
                # Get the access token from the service
                token = jira_service.get_oauth2_token()
                if not token or "access_token" not in token:
                    raise ValueError("No valid access token available")
                
                # Try to access a simpler endpoint: serverInfo
                import requests
                headers = {
                    "Authorization": f"Bearer {token['access_token']}",
                    "Accept": "application/json"
                }
                
                # Try to get server info
                url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/2/serverInfo"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                server_info = response.json()
                
                # Create a minimal user info response
                # We don't have actual user info, but we can at least show the server is accessible
                return {
                    "displayName": "Jira User",
                    "accountId": "unknown",
                    "emailAddress": "unknown",
                    "active": True,
                    "serverInfo": server_info,
                    "note": "Limited user information available due to scope restrictions"
                }
            except Exception as inner_e:
                logger.error(f"Failed to get even basic Jira server info: {str(inner_e)}")
                raise ValueError(f"Cannot access Jira user API with current permissions: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Jira user info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Jira user info: {str(e)}"
        )
