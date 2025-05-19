#!/usr/bin/env python3
"""
OAuth token monitoring API endpoints

This module provides endpoints for monitoring and managing OAuth tokens.
It includes token status reporting, manual refresh, and history tracking.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.services.jira_service import jira_service

router = APIRouter(
    prefix="/oauth",
    tags=["oauth"],
    responses={404: {"description": "Not found"}},
)


class TokenStatus(BaseModel):
    """Model for token status response"""
    status: str  # "active", "expired", "refreshing", "error"
    expires_in_seconds: Optional[int] = None
    expires_in_formatted: Optional[str] = None
    expires_at: Optional[str] = None
    refresh_in_seconds: Optional[int] = None
    refresh_in_formatted: Optional[str] = None
    refresh_status: Optional[str] = None  # "waiting", "ready", "in_progress"
    last_refresh: Optional[str] = None
    next_scheduled_check: Optional[str] = None
    refreshes_attempted: Optional[int] = None
    refreshes_succeeded: Optional[int] = None
    refreshes_failed: Optional[int] = None
    message: Optional[str] = None


class TokenEvent(BaseModel):
    """Model for token event history"""
    event_type: str
    message: str
    timestamp: str


class Project(BaseModel):
    """Model for Jira project"""
    id: str
    key: str
    name: str


class Issue(BaseModel):
    """Model for Jira issue"""
    key: str
    summary: str
    status: str
    assignee: Optional[str] = None
    updated: Optional[str] = None


@router.get("/token/status", response_model=TokenStatus)
async def get_token_status():
    """Get the current OAuth token status"""
    # If token service is not initialized
    if not jira_service._token_service:
        raise HTTPException(
            status_code=404,
            detail="OAuth token service not initialized. Please check your configuration."
        )
    
    try:
        # Get the current token
        token = jira_service.get_oauth2_token()
        
        # Check if token exists
        if not token:
            return TokenStatus(
                status="error",
                message="No OAuth token available"
            )
        
        # Build response
        response = TokenStatus(status="unknown")
        
        # Calculate expiration information if available
        if 'expires_at' in token:
            expires_at = token['expires_at']
            current_time = datetime.now().timestamp()
            time_remaining = expires_at - current_time
            
            # Calculate refresh time (default to 10 minutes before expiration)
            refresh_threshold = jira_service._token_service.refresh_threshold
            refresh_at = expires_at - refresh_threshold
            time_to_refresh = refresh_at - current_time
            
            if time_remaining > 0:
                response.status = "active"
                response.expires_in_seconds = int(time_remaining)
                response.expires_in_formatted = str(time_remaining)
            else:
                response.status = "expired"
                response.message = "Token has expired"
            
            # Add refresh status
            if time_to_refresh > 0:
                response.refresh_status = "waiting"
                response.refresh_in_seconds = int(time_to_refresh)
                response.refresh_in_formatted = str(time_to_refresh)
            else:
                response.refresh_status = "ready"
            
            # Add absolute times
            response.expires_at = datetime.fromtimestamp(expires_at).isoformat()
        
        # Add token service stats if available
        token_service = jira_service._token_service
        if token_service:
            stats = token_service.stats
            
            if stats["last_refresh"]:
                response.last_refresh = stats["last_refresh"].isoformat()
            
            if stats["next_scheduled_check"]:
                response.next_scheduled_check = stats["next_scheduled_check"].isoformat()
            
            response.refreshes_attempted = stats["refreshes_attempted"]
            response.refreshes_succeeded = stats["refreshes_succeeded"]
            response.refreshes_failed = stats["refreshes_failed"]
        
        return response
        
    except Exception as e:
        # Log the error
        import logging
        logging.error(f"Error getting token status: {str(e)}")
        
        # Return error response
        return TokenStatus(
            status="error",
            message=f"Failed to get token status: {str(e)}"
        )


@router.post("/token/refresh", response_model=TokenStatus)
async def refresh_token(background_tasks: BackgroundTasks):
    """Manually refresh the OAuth token"""
    # If token service is not initialized
    if not jira_service._token_service:
        raise HTTPException(
            status_code=404,
            detail="OAuth token service not initialized. Please check your configuration."
        )
    
    try:
        # Queue the refresh in a background task
        background_tasks.add_task(jira_service.refresh_oauth2_token, force=True)
        
        # Return immediate response
        return TokenStatus(
            status="refreshing",
            message="Token refresh initiated"
        )
        
    except Exception as e:
        import logging
        logging.error(f"Error refreshing token: {str(e)}")
        
        # Return error response
        return TokenStatus(
            status="error", 
            message=f"Failed to refresh token: {str(e)}"
        )


@router.get("/token/events", response_model=List[TokenEvent])
async def get_token_events():
    """Get the OAuth token event history"""
    # If token service is not initialized
    if not jira_service._token_service:
        raise HTTPException(
            status_code=404,
            detail="OAuth token service not initialized. Please check your configuration."
        )
    
    try:
        # Get the event history
        events = []
        
        # Convert event objects to the response model
        with jira_service._token_service._lock:
            for event in jira_service._token_service._event_history:
                events.append(TokenEvent(
                    event_type=event.event_type,
                    message=event.message,
                    timestamp=event.timestamp.isoformat()
                ))
        
        return events
        
    except Exception as e:
        import logging
        logging.error(f"Error getting token events: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get token events: {str(e)}"
        )


@router.get("/jira/projects", response_model=List[Project])
async def get_jira_projects():
    """Get a list of Jira projects using the OAuth token"""
    try:
        # Check if Jira service is connected
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
        
    except Exception as e:
        import logging
        logging.error(f"Error getting Jira projects: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Jira projects: {str(e)}"
        )


@router.get("/jira/issues", response_model=List[Issue])
async def get_jira_issues(project_key: str = Query(None, description="Jira project key"),
                         max_results: int = Query(10, description="Maximum number of issues to return")):
    """Get a list of Jira issues using the OAuth token"""
    try:
        # Check if Jira service is connected
        if not jira_service.is_connected():
            raise HTTPException(
                status_code=500,
                detail="Not connected to Jira. Please check your OAuth token."
            )
        
        # Build JQL query
        jql = f"project = {project_key}" if project_key else "order by updated DESC"
        
        # Search for issues using the token
        result = jira_service.search_issues(jql=jql, max_results=max_results)
        
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
        
    except Exception as e:
        import logging
        logging.error(f"Error getting Jira issues: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Jira issues: {str(e)}"
        )
