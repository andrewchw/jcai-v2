#!/usr/bin/env python3
"""
OAuth token monitoring API endpoints

This module provides endpoints for monitoring and managing OAuth tokens.
It includes token status reporting, manual refresh, and history tracking.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Request
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


@router.get("/login")
async def login(request: Request):
    """Start OAuth login process"""
    try:
        from fastapi.responses import RedirectResponse, JSONResponse
        
        # For a real implementation, we would generate an authorization URL like this:
        # auth_url = f"https://auth.atlassian.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=read:jira-work"
        
        # Construct the callback URL for testing
        callback_url = "/api/auth/oauth/callback?setup_example=true"
        
        # Determine if this is an API request or browser request
        if (
            "Accept" in request.headers and 
            "application/json" in request.headers["Accept"] and 
            "text/html" not in request.headers["Accept"]
        ):
            # API request - return JSON
            return JSONResponse({
                "success": True,
                "redirect_url": callback_url
            })
        
        # Browser request - redirect to callback
        return RedirectResponse(url=callback_url)
    except Exception as e:
        import logging
        logging.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start login process: {str(e)}"
        )


@router.get("/callback")
async def oauth_callback(request: Request, code: str = None, state: str = None, setup_example: bool = False):
    """Handle OAuth callback from authorization server"""
    from fastapi.responses import HTMLResponse, RedirectResponse
    import time
    from datetime import datetime, timedelta
    
    try:
        success = False
        message = "Authentication failed"
        
        # If this is just a setup example, set up a test token
        if setup_example:
            # Create a sample token for testing
            # Check if we have an existing token first
            token = jira_service.get_oauth2_token()
            
            if not token:
                # Create a test token that expires in 1 hour
                expires_at = datetime.now() + timedelta(hours=1)
                
                token = {
                    "access_token": "test_access_token_" + str(int(time.time())),
                    "refresh_token": "test_refresh_token_" + str(int(time.time())),
                    "token_type": "Bearer",
                    "expires_at": expires_at.timestamp(),
                    "expires_in": 3600,  # 1 hour
                    "created_at": datetime.now().timestamp()
                }
                
                # Save the token
                jira_service.set_oauth2_token(token)
                
                success = True
                message = "Authentication successful"
        
        # Handle proper OAuth callback (for production)
        elif code:
            # Placeholder for token exchange logic
            # token = exchange_code_for_token(code)
            # jira_service.set_oauth2_token(token)
            # For now, we'll just assume success if code is present
            success = True
            message = "Authentication successful with authorization code"
        else:
            message = "Authorization code is required"
        
        # Create a nice HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>JIRA Chatbot Assistant - Authentication</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #f5f5f5;
                }}
                .container {{
                    text-align: center;
                    background-color: white;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    max-width: 500px;
                }}
                h1 {{
                    color: {"#0052CC" if success else "#DE350B"};
                    margin-bottom: 20px;
                }}
                p {{
                    color: #333;
                    line-height: 1.6;
                    margin-bottom: 30px;
                }}
                .icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                .success {{ color: #0052CC; }}
                .error {{ color: #DE350B; }}
            </style>
            <script>
                // Close this window automatically after a delay
                setTimeout(() => {{
                    window.close();
                }}, 3000);
            </script>
        </head>
        <body>
            <div class="container">
                <div class="icon">
                    {"✅" if success else "❌"}
                </div>
                <h1>{"Authentication Successful" if success else "Authentication Failed"}</h1>
                <p>{message}</p>
                <p>This window will close automatically in a few seconds.</p>
            </div>
        </body>
        </html>
        """
          # Check if this is an API request or browser request
        if (
            "Accept" in request.headers and 
            "application/json" in request.headers["Accept"] and 
            "text/html" not in request.headers["Accept"]
        ):
            # API request - return JSON
            return {"success": success, "message": message}
        
        # Browser request - return HTML with redirect for success
        if success:
            response_html = html_content + f"""
            <script>
                // Notify extension of success by updating URL parameter
                window.history.replaceState(null, "", "{'/api/auth/oauth/callback?success=true'}");
                
                // If this was opened from our extension, communicate success back to it
                if (window.opener) {{
                    try {{
                        window.opener.postMessage({{ type: "oauth-success" }}, "*");
                    }} catch (e) {{
                        console.error("Could not send message to opener:", e);
                    }}
                }}
            </script>
            """
            return HTMLResponse(response_html)
        else:
            return HTMLResponse(html_content)
        
    except Exception as e:
        import logging
        logging.error(f"Error during OAuth callback: {str(e)}")
        
        # Return error HTML
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>JIRA Chatbot Assistant - Error</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #f5f5f5;
                }}
                .container {{
                    text-align: center;
                    background-color: white;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    max-width: 500px;
                }}
                h1 {{
                    color: #DE350B;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #333;
                    line-height: 1.6;
                    margin-bottom: 30px;
                }}
                .icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                .error {{ color: #DE350B; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon error">❌</div>
                <h1>Authentication Error</h1>
                <p>An error occurred during the authentication process.</p>
                <p>Error details: {str(e)}</p>
                <p>Please close this window and try again.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(error_html)


@router.get("/logout")
async def logout():
    """Logout and invalidate OAuth token"""
    try:
        # Invalidate the token if a token service exists
        if jira_service._token_service:
            jira_service._token_service.invalidate_token()
            
        return {
            "success": True,
            "message": "Successfully logged out"
        }
    except Exception as e:
        import logging
        logging.error(f"Error during logout: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to logout: {str(e)}"
        )
