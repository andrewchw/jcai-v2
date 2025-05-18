import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
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

# Load environment variables
load_dotenv()

# OAuth2 settings from environment variables
client_id = os.getenv("JIRA_OAUTH_CLIENT_ID")
client_secret = os.getenv("JIRA_OAUTH_CLIENT_SECRET")
redirect_uri = os.getenv("JIRA_OAUTH_CALLBACK_URL")

# Jira OAuth2 endpoints
authorization_base_url = "https://auth.atlassian.com/authorize"
token_url = "https://auth.atlassian.com/oauth/token"

# Create FastAPI app
app = FastAPI(title="Jira OAuth2 Example")

@app.get("/")
async def root():
    """Home page with login link"""
    return {"message": "Welcome to Jira OAuth2 Example", "login_url": "/login"}

@app.get("/login")
async def login():
    """Start OAuth2 flow by redirecting to Jira login"""
    # Define the requested scopes
    scope = [
        "read:jira-user",
        "read:jira-work",
        "write:jira-work"
    ]
    audience = "api.atlassian.com"
    
    # Create OAuth2 session
    jira_oauth = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    
    # Generate authorization URL
    authorization_url, state = jira_oauth.authorization_url(
        authorization_base_url,
        audience=audience
    )
    
    logger.info(f"Authorization URL: {authorization_url}")
    
    # Store the state for later verification
    # In a real app, you'd store this in a user session
    with open("oauth_state.txt", "w") as f:
        f.write(state)
    
    # Redirect user to Jira for authorization
    return RedirectResponse(authorization_url)

@app.get("/callback")
async def callback(request: Request):
    """Handle OAuth2 callback from Jira"""
    # Get query parameters from the request
    params = dict(request.query_params)
    
    # Read the stored state
    try:
        with open("oauth_state.txt", "r") as f:
            state = f.read().strip()
    except:
        state = None
        logger.warning("Could not read stored state")
    
    # Complete OAuth flow
    jira_oauth = OAuth2Session(client_id, state=state, redirect_uri=redirect_uri)
    
    # Exchange code for token
    try:
        token = jira_oauth.fetch_token(
            token_url,
            client_secret=client_secret,
            authorization_response=str(request.url)
        )
        
        logger.info("OAuth token obtained successfully")
        
        # Get accessible resources (Jira Cloud instances)
        resources = get_accessible_resources(token)
        
        if not resources:
            return {"error": "No accessible Jira resources found"}
        
        # Use the first cloud ID for demonstration
        cloud_id = resources[0]["id"]
        
        # Get projects using the token
        projects = get_projects(token, cloud_id)
        
        return {
            "status": "success",
            "message": "OAuth2 authentication successful",
            "cloud_id": cloud_id,
            "projects": projects,
            "token_info": {
                "access_token": token["access_token"][:10] + "...", # Truncated for security
                "token_type": token["token_type"],
                "expires_in": token.get("expires_in"),
                "scope": token.get("scope")
            }
        }
        
    except Exception as e:
        logger.exception(f"Error completing OAuth flow: {str(e)}")
        return {"error": f"OAuth authentication failed: {str(e)}"}

def get_accessible_resources(token):
    """Get accessible Jira Cloud instances"""
    import requests
    
    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.atlassian.com/oauth/token/accessible-resources",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting accessible resources: {str(e)}")
        return None

def get_projects(token, cloud_id):
    """Get projects using Atlassian Python API"""
    try:
        # Create OAuth2 dictionary for Atlassian Python API
        oauth2_dict = {
            "client_id": client_id,
            "token": {
                "access_token": token["access_token"],
                "token_type": "Bearer"
            }
        }
        
        # Initialize Jira client with OAuth2
        jira = Jira(
            url=f"https://api.atlassian.com/ex/jira/{cloud_id}",
            oauth2=oauth2_dict,
            cloud=True
        )
        
        # Get projects
        projects = jira.projects()
        
        # Return just the project names and keys for simplicity
        return [{"name": p["name"], "key": p["key"]} for p in projects]
    
    except Exception as e:
        logger.exception(f"Error getting projects: {str(e)}")
        return []

if __name__ == "__main__":
    if not all([client_id, client_secret, redirect_uri]):
        logger.error("Missing required OAuth2 configuration.")
        logger.error("Please ensure JIRA_OAUTH_CLIENT_ID, JIRA_OAUTH_CLIENT_SECRET, and JIRA_OAUTH_CALLBACK_URL are set in .env")
        sys.exit(1)
    
    logger.info("Starting OAuth2 example server...")
    uvicorn.run(app, host="localhost", port=8000)
