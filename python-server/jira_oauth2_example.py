#!/usr/bin/env python3
"""
Jira OAuth 2.0 Authentication Example

This script demonstrates OAuth 2.0 authentication with Atlassian Jira Cloud using the Atlassian Python API.
It provides a FastAPI application that handles the OAuth 2.0 flow including:

1. Redirecting users to Atlassian login page
2. Processing the callback with authorization code
3. Exchanging authorization code for access token
4. Refreshing tokens when they expire
5. Storing tokens securely
6. Using tokens to access the Jira API

For more information, see:
https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/
"""

import os
import json
import logging
import sys
import secrets
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from requests_oauthlib import OAuth2Session
from atlassian import Jira
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# OAuth2 settings from environment variables
CLIENT_ID = os.getenv("JIRA_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("JIRA_OAUTH_CLIENT_SECRET")
REDIRECT_URI = os.getenv("JIRA_OAUTH_CALLBACK_URL")
TOKEN_FILE = os.getenv("TOKEN_FILE", "oauth_token.json")

# Jira OAuth2 endpoints
AUTHORIZATION_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"

# OAuth2 scopes - adjust as needed
SCOPES = [
    "read:jira-user",
    "read:jira-work",
    "write:jira-work",
    "manage:jira-project",
    "manage:jira-configuration",
    "offline_access"
]

# Create FastAPI app
app = FastAPI(
    title="Jira OAuth2 Example",
    description="An example OAuth 2.0 implementation for Atlassian Jira Cloud",
    version="0.1.0"
)

# OAuth2 security scheme for Swagger UI
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=AUTHORIZATION_URL,
    tokenUrl=TOKEN_URL,
    scopes={scope: scope for scope in SCOPES}
)

# Store for session state and tokens (use a database in production)
session_store = {}


def load_token():
    """Load OAuth token from file"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load token: {str(e)}")
    return None


def save_token(token):
    """Save OAuth token to file"""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token, f)
        return True
    except Exception as e:
        logger.error(f"Could not save token: {str(e)}")
        return False


def refresh_token(token):
    """Refresh the OAuth 2.0 token if it's expired"""
    try:
        # Create a new OAuth2 session
        oauth = OAuth2Session(CLIENT_ID, token=token)
        
        # Check if token is expired or about to expire (within 60 seconds)
        if 'expires_at' in token:
            expires_at = token['expires_at']
            if datetime.now().timestamp() > (expires_at - 60):
                logger.info("Token is expired or about to expire, refreshing...")
                
                # Refresh the token
                new_token = oauth.refresh_token(
                    TOKEN_URL,
                    refresh_token=token['refresh_token'],
                    client_id=CLIENT_ID,
                    client_secret=CLIENT_SECRET
                )
                
                # Save the new token
                save_token(new_token)
                return new_token
        
        return token
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return None


def get_jira_client(cloud_id, token=None):
    """Create a Jira client using OAuth 2.0 authentication"""
    if not token:
        token = load_token()
    
    if token:
        # Try to refresh the token if needed
        token = refresh_token(token)
        
        # Create OAuth2 dictionary for Atlassian Python API
        oauth2_dict = {
            "client_id": CLIENT_ID,
            "token": {
                "access_token": token["access_token"],
                "token_type": "Bearer"
            }
        }
        
        # Initialize Jira client with OAuth2
        return Jira(
            url=f"https://api.atlassian.com/ex/jira/{cloud_id}",
            oauth2=oauth2_dict,
            cloud=True
        )
    
    return None


@app.get("/")
async def root():
    """Home page with login link"""
    # Check if we already have a token
    token = load_token()
    
    if token:
        # Check if the token is still valid
        try:
            # Get accessible resources
            resources = get_accessible_resources(token)
            if resources:
                return {
                    "message": "You are already authenticated with Jira",
                    "status": "authenticated",
                    "resources": resources,
                    "actions": {
                        "get_projects": "/projects",
                        "logout": "/logout"
                    }
                }
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            # Continue with login flow
    
    return {
        "message": "Welcome to Jira OAuth2 Example",
        "status": "unauthenticated",
        "actions": {
            "login": "/login"
        }
    }


@app.get("/login")
async def login():
    """Start OAuth2 flow by redirecting to Jira login"""
    # Generate a random state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Define the requested scopes and audience
    audience = "api.atlassian.com"
    
    # Create OAuth2 session
    jira_oauth = OAuth2Session(
        CLIENT_ID,
        scope=SCOPES,
        redirect_uri=REDIRECT_URI
    )    # Generate authorization URL
    authorization_url, state = jira_oauth.authorization_url(
        AUTHORIZATION_URL,
        audience=audience
        # Note: Atlassian doesn't support standard offline_access scope or parameters
        # Refresh tokens are controlled in the Atlassian Developer Console settings
    )
    
    logger.info(f"Authorization URL: {authorization_url}")
    
    # Store the state in our session store
    session_store["oauth_state"] = state
    
    # Redirect user to Jira for authorization
    return RedirectResponse(authorization_url)


@app.get("/callback")
async def callback(request: Request):
    """Handle OAuth2 callback from Jira"""
    # Get query parameters from the request
    params = dict(request.query_params)
    
    # Check for errors
    if "error" in params:
        error = params["error"]
        error_description = params.get("error_description", "Unknown error")
        logger.error(f"OAuth error: {error} - {error_description}")
        return {
            "status": "error",
            "error": error,
            "error_description": error_description
        }
    
    # Get the authorization code
    code = params.get("code")
    if not code:
        return {
            "status": "error",
            "error": "missing_code",
            "error_description": "Authorization code not found in callback"
        }
    
    # Reconstruct the authentication response URL
    callback_url = str(request.url)
    
    try:
        # Create OAuth2 session
        jira_oauth = OAuth2Session(
            CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            state=session_store.get("oauth_state")
        )
        
        # Exchange code for token
        token = jira_oauth.fetch_token(
            TOKEN_URL,
            code=code,
            client_secret=CLIENT_SECRET,
            include_client_id=True
        )
        
        logger.info("OAuth token obtained successfully")
        
        # Save the token
        save_token(token)
        
        # Get accessible resources (Jira Cloud instances)
        resources = get_accessible_resources(token)
        
        if not resources:
            return {
                "status": "error",
                "error": "no_resources",
                "error_description": "No accessible Jira resources found"
            }
        
        # Use the first cloud ID for demonstration
        cloud_id = resources[0]["id"]
        site_name = resources[0]["name"]
        
        # Get projects using the token
        jira = get_jira_client(cloud_id, token)
        projects = jira.projects()
        return {
            "status": "success",
            "message": "OAuth2 authentication successful",
            "site": site_name,
            "cloud_id": cloud_id,
            "projects_count": len(projects),
            "projects": [{"key": p["key"], "name": p["name"]} for p in projects[:5]],
            "token_info": {
                "access_token": token["access_token"][:10] + "...",  # Truncated for security
                "token_type": token["token_type"],
                "expires_in": token.get("expires_in"),
                "scope": token.get("scope", []) if isinstance(token.get("scope"), list) else token.get("scope", "").split()
            }
        }
        
    except Exception as e:
        logger.exception(f"Error completing OAuth flow: {str(e)}")
        return {
            "status": "error",
            "error": "oauth_error",
            "error_description": f"OAuth authentication failed: {str(e)}"
        }


def get_accessible_resources(token):
    """Get accessible Jira Cloud instances"""
    import requests
    
    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(RESOURCES_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting accessible resources: {str(e)}")
        return None


@app.get("/projects")
async def get_projects():
    """Get projects from Jira"""
    token = load_token()
    
    if not token:
        return RedirectResponse(url="/login")
    
    try:
        # Refresh token if needed
        token = refresh_token(token)
        
        # Get accessible resources
        resources = get_accessible_resources(token)
        
        if not resources:
            return {
                "status": "error",
                "error": "no_resources",
                "error_description": "No accessible Jira resources found"
            }
        
        # Use the first cloud ID
        cloud_id = resources[0]["id"]
        site_name = resources[0]["name"]
        
        # Get projects using the token
        jira = get_jira_client(cloud_id, token)
        projects = jira.projects()
        
        return {
            "status": "success",
            "site": site_name,
            "cloud_id": cloud_id,
            "count": len(projects),
            "projects": [
                {
                    "key": project["key"],
                    "name": project["name"],
                    "id": project["id"]
                }
                for project in projects
            ]
        }
        
    except Exception as e:
        logger.exception(f"Error getting projects: {str(e)}")
        return {
            "status": "error",
            "error": "api_error",
            "error_description": f"Error getting projects: {str(e)}"
        }


@app.get("/issues")
async def get_issues(project_key: str = None, max_results: int = 10):
    """Get issues from a Jira project"""
    token = load_token()
    
    if not token:
        return RedirectResponse(url="/login")
    
    try:
        # Refresh token if needed
        token = refresh_token(token)
        
        # Get accessible resources
        resources = get_accessible_resources(token)
        
        if not resources:
            return {
                "status": "error",
                "error": "no_resources",
                "error_description": "No accessible Jira resources found"
            }
        
        # Use the first cloud ID
        cloud_id = resources[0]["id"]
        
        # Get issues using the token
        jira = get_jira_client(cloud_id, token)
        
        # Build JQL query
        jql = f"project = {project_key}" if project_key else "order by updated DESC"
        
        # Get issues
        issues = jira.jql(jql, limit=max_results)
        
        return {
            "status": "success",
            "count": len(issues["issues"]),
            "total": issues["total"],
            "issues": [
                {
                    "key": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "status": issue["fields"]["status"]["name"],
                    "assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"].get("assignee") else None,
                    "updated": issue["fields"]["updated"]
                }
                for issue in issues["issues"]
            ]
        }
        
    except Exception as e:
        logger.exception(f"Error getting issues: {str(e)}")
        return {
            "status": "error",
            "error": "api_error",
            "error_description": f"Error getting issues: {str(e)}"
        }


@app.get("/logout")
async def logout():
    """Log out by removing the stored token"""
    if os.path.exists(TOKEN_FILE):
        try:
            os.remove(TOKEN_FILE)
            return {
                "status": "success",
                "message": "You have been logged out successfully"
            }
        except Exception as e:
            logger.error(f"Error removing token file: {str(e)}")
            return {
                "status": "error",
                "error": "logout_error",
                "error_description": f"Error logging out: {str(e)}"
            }
    else:
        return {
            "status": "success",
            "message": "You were not logged in"
        }


@app.get("/token")
async def show_token():
    """Show the current OAuth token (for debugging)"""
    token = load_token()
    
    if token:
        # Mask sensitive parts
        if "access_token" in token:
            token["access_token"] = token["access_token"][:10] + "..."
        if "refresh_token" in token:
            token["refresh_token"] = token["refresh_token"][:5] + "..."
        
        return {
            "status": "success",
            "token": token
        }
    else:
        return {
            "status": "error",
            "error": "no_token",
            "error_description": "No OAuth token found"
        }


if __name__ == "__main__":
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        logger.error("Missing required OAuth2 configuration.")
        logger.error("Please ensure JIRA_OAUTH_CLIENT_ID, JIRA_OAUTH_CLIENT_SECRET, and JIRA_OAUTH_CALLBACK_URL are set in .env")
        sys.exit(1)
      # Load port from environment variables
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "localhost")
    
    # Add fallback ports in case the primary port is in use
    fallback_ports = [8081, 8082, 8083, 8084, 8085]
    
    logger.info("Starting OAuth2 example server...")
    logger.info(f"Callback URL is set to: {REDIRECT_URI}")
    logger.info("Please make sure this matches the Callback URL in your Atlassian OAuth 2.0 application settings")
    
    # Try to start the server on the configured port
    try:
        logger.info(f"Attempting to start server on http://{host}:{port}")
        logger.info(f"Navigate to http://{host}:{port} to begin the OAuth flow")
        uvicorn.run(app, host=host, port=port)
    except OSError as e:
        # If the port is already in use, try fallback ports
        if e.errno == 10048:  # Socket address already in use
            logger.warning(f"Port {port} is already in use. Trying fallback ports...")
            
            for fallback_port in fallback_ports:
                try:
                    logger.info(f"Attempting to start server on http://{host}:{fallback_port}")
                    logger.info(f"NOTE: This is different from the registered callback URL!")
                    logger.info(f"Navigate to http://{host}:{fallback_port} to begin the OAuth flow")
                    uvicorn.run(app, host=host, port=fallback_port)
                    break
                except OSError:
                    logger.warning(f"Port {fallback_port} is also in use. Trying next port...")
            else:
                logger.error("All ports are in use. Please free up a port or modify the script to use a different port.")
                sys.exit(1)
        else:
            # Re-raise any other exception
            raise
