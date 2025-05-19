#!/usr/bin/env python3
"""
Jira OAuth 2.0 Authentication Troubleshooter

This script helps troubleshoot OAuth 2.0 authentication issues with Jira.
It provides a clean slate by removing any existing token files and 
running through the authentication process with detailed logging.
"""

import os
import json
import logging
import sys
import secrets
from datetime import datetime, timedelta
import time
import webbrowser

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from requests_oauthlib import OAuth2Session
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
from dotenv import load_dotenv
load_dotenv()

# OAuth2 settings
CLIENT_ID = os.getenv("JIRA_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("JIRA_OAUTH_CLIENT_SECRET")
REDIRECT_URI = os.getenv("JIRA_OAUTH_CALLBACK_URL")
TOKEN_FILE = os.getenv("TOKEN_STORAGE_PATH", "oauth_token.json")
AUTH_BASE_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
API_URL = "https://api.atlassian.com/ex/jira/{}/rest/api/3"

# Check for required environment variables
required_vars = ["JIRA_OAUTH_CLIENT_ID", "JIRA_OAUTH_CLIENT_SECRET", "JIRA_OAUTH_CALLBACK_URL"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please set these variables in your .env file or environment.")
    sys.exit(1)

# Clean up old token file if it exists
if os.path.exists(TOKEN_FILE):
    logger.info(f"Removing existing token file: {TOKEN_FILE}")
    try:
        os.remove(TOKEN_FILE)
        logger.info("Token file removed successfully.")
    except Exception as e:
        logger.error(f"Failed to remove token file: {str(e)}")

# Create FastAPI app
app = FastAPI(title="Jira OAuth2 Troubleshooter")

# Simple in-memory session store (for demo purposes only)
session_store = {}

def save_token(token):
    """Save the OAuth token to file with improved error handling"""
    try:
        # Add some metadata to help with troubleshooting
        token['saved_at'] = datetime.now().isoformat()
        
        if 'expires_at' in token:
            expiry_time = datetime.fromtimestamp(token['expires_at'])
            token['expiry_iso'] = expiry_time.isoformat()
        
        # Pretty format for readability
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token, f, indent=2)
        logger.info(f"Token saved successfully to {TOKEN_FILE}")
        return True
    except Exception as e:
        logger.error(f"Could not save token: {str(e)}")
        return False

@app.get("/")
def home():
    """Home page with instructions and login link"""
    return HTMLResponse("""
    <html>
        <head><title>Jira OAuth2 Troubleshooter</title></head>
        <body>
            <h1>Jira OAuth2 Authentication Troubleshooter</h1>
            <p>This tool helps diagnose issues with Jira OAuth2 authentication.</p>
            <p>Click the button below to start the authentication process:</p>
            <a href="/login" style="display: inline-block; padding: 10px 20px; background-color: #0052CC; color: white; text-decoration: none; border-radius: 3px;">Start OAuth Flow</a>
        </body>
    </html>
    """)

@app.get("/login")
def login():
    """Initiate the OAuth2 authorization flow"""
    # Generate a secure random state
    state = secrets.token_urlsafe(16)
    session_store["oauth_state"] = state
    
    # Define the scope
    scope = [
        "read:jira-user",
        "read:jira-work",
        "write:jira-work",
        "manage:jira-project",
        "manage:jira-configuration",
        "offline_access"  # Important for refresh tokens
    ]
    
    # Create OAuth2 session
    oauth = OAuth2Session(
        CLIENT_ID, 
        redirect_uri=REDIRECT_URI, 
        scope=scope, 
        state=state
    )
    
    # Get authorization URL
    authorization_url, state = oauth.authorization_url(
        AUTH_BASE_URL,
        audience="api.atlassian.com"
    )
    
    logger.info(f"Authorization URL: {authorization_url}")
    logger.info(f"State: {state}")
    
    # Store state for validation in the callback
    session_store["oauth_state"] = state
    
    # Open browser automatically
    webbrowser.open(authorization_url)
    
    return RedirectResponse(authorization_url)

@app.get("/callback")
async def callback(request: Request):
    """Handle the OAuth callback"""
    # Get query parameters
    params = dict(request.query_params)
    logger.info(f"Received callback with parameters: {params}")
    
    # Validate state
    state = params.get("state")
    if not state or state != session_store.get("oauth_state"):
        logger.error(f"State mismatch! Expected: {session_store.get('oauth_state')}, Got: {state}")
        return JSONResponse({
            "status": "error",
            "error": "invalid_state",
            "error_description": "State parameter does not match"
        })
    
    # Get authorization code
    code = params.get("code")
    if not code:
        logger.error("No authorization code found in callback parameters")
        return JSONResponse({
            "status": "error",
            "error": "missing_code",
            "error_description": "Authorization code not found in callback"
        })
    
    # Extract the full callback URL
    callback_url = str(request.url)
    logger.info(f"Full callback URL: {callback_url}")
    
    try:
        # Create OAuth2 session
        jira_oauth = OAuth2Session(
            CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            state=session_store.get("oauth_state")
        )
        
        # Log the data we're sending for the token request
        logger.info(f"Exchanging code for token...")
        logger.info(f"Code: {code[:10]}...{code[-10:]} (truncated)")  # Partial code for security
        logger.info(f"Redirect URI: {REDIRECT_URI}")
        
        # Exchange code for token with short timeout
        start_time = time.time()
        token = jira_oauth.fetch_token(
            TOKEN_URL,
            code=code,
            client_secret=CLIENT_SECRET,
            include_client_id=True,
            timeout=30  # 30 second timeout
        )
        elapsed_time = time.time() - start_time
        
        logger.info(f"Token request completed in {elapsed_time:.2f} seconds")
        logger.info("OAuth token obtained successfully!")
        
        # Save the token
        save_token(token)
        
        # Get access token details
        token_type = token.get("token_type", "unknown")
        expires_in = token.get("expires_in", "unknown")
        scope = token.get("scope", [])
        if isinstance(scope, str):
            scope = scope.split()
        
        # Check if we have a refresh token
        has_refresh = "refresh_token" in token
        
        # Calculate expiry time
        expiry_time = "unknown"
        if "expires_at" in token:
            expiry_time = datetime.fromtimestamp(token["expires_at"]).strftime("%Y-%m-%d %H:%M:%S")
        
        # Get accessible resources (Jira Cloud instances)
        logger.info("Fetching accessible Jira resources...")
        resources = None
        cloud_id = None
        site_name = None
        
        try:
            headers = {
                "Authorization": f"Bearer {token['access_token']}",
                "Accept": "application/json"
            }
            import requests
            response = requests.get(RESOURCES_URL, headers=headers)
            response.raise_for_status()
            resources = response.json()
            
            if resources:
                cloud_id = resources[0]["id"]
                site_name = resources[0]["name"]
                logger.info(f"Found Jira site: {site_name} (Cloud ID: {cloud_id})")
                
                # Save cloud ID to .env file
                with open(".env", "r") as f:
                    env_content = f.read()
                
                if "ATLASSIAN_OAUTH_CLOUD_ID" in env_content:
                    env_content = env_content.replace(
                        f"ATLASSIAN_OAUTH_CLOUD_ID={os.getenv('ATLASSIAN_OAUTH_CLOUD_ID', '')}",
                        f"ATLASSIAN_OAUTH_CLOUD_ID={cloud_id}"
                    )
                else:
                    env_content += f"\n# Required for the server AFTER running --oauth-setup (this ID is printed by the setup wizard):\nATLASSIAN_OAUTH_CLOUD_ID={cloud_id}\n"
                
                with open(".env", "w") as f:
                    f.write(env_content)
                
                logger.info(f"Updated .env file with ATLASSIAN_OAUTH_CLOUD_ID={cloud_id}")
            else:
                logger.warning("No accessible Jira resources found!")
        except Exception as e:
            logger.error(f"Error fetching Jira resources: {str(e)}")
        
        # Return success page with token info
        return HTMLResponse(f"""
        <html>
            <head><title>OAuth2 Success</title></head>
            <body>
                <h1 style="color: green;">Authentication Successful! ✅</h1>
                <h2>Token Details:</h2>
                <ul>
                    <li>Token Type: {token_type}</li>
                    <li>Expires In: {expires_in} seconds</li>
                    <li>Expiry Time: {expiry_time}</li>
                    <li>Has Refresh Token: {'Yes ✅' if has_refresh else 'No ❌'}</li>
                    <li>Scopes: {', '.join(scope)}</li>
                </ul>
                
                <h2>Jira Site Information:</h2>
                <ul>
                    <li>Site Name: {site_name if site_name else 'Not found'}</li>
                    <li>Cloud ID: {cloud_id if cloud_id else 'Not found'}</li>
                </ul>
                
                <p><strong>Token file saved to:</strong> {os.path.abspath(TOKEN_FILE)}</p>
                <p>You can now close this window and continue with the server.</p>
                
                <h3>Next Steps:</h3>
                <p>Run your server with:</p>
                <pre>python python-server/run.py</pre>
            </body>
        </html>
        """)
        
    except Exception as e:
        logger.exception(f"Error completing OAuth flow: {str(e)}")
        return HTMLResponse(f"""
        <html>
            <head><title>OAuth2 Error</title></head>
            <body>
                <h1 style="color: red;">Authentication Error! ❌</h1>
                <p><strong>Error:</strong> {str(e)}</p>
                
                <h2>Troubleshooting Steps:</h2>
                <ol>
                    <li>Check that your JIRA_OAUTH_CLIENT_ID, JIRA_OAUTH_CLIENT_SECRET, and JIRA_OAUTH_CALLBACK_URL are correct</li>
                    <li>Verify that your OAuth app is properly configured in the Atlassian Developer Console</li>
                    <li>Make sure the callback URL matches exactly what's configured in the Atlassian Developer Console</li>
                    <li>Check that your clock is synchronized (time skew can cause authentication issues)</li>
                    <li>Try again with a fresh browser session (clear cookies)</li>
                </ol>
                
                <p>You can <a href="/login">try again</a> or close this window.</p>
            </body>
        </html>
        """)

if __name__ == "__main__":
    # Display startup information
    logger.info("=" * 60)
    logger.info("Jira OAuth2 Authentication Troubleshooter")
    logger.info("=" * 60)
    logger.info(f"Client ID: {CLIENT_ID[:5]}...{CLIENT_ID[-5:] if CLIENT_ID else ''}")
    logger.info(f"Callback URL: {REDIRECT_URI}")
    logger.info(f"Token storage path: {TOKEN_FILE}")
    logger.info("Starting server on http://localhost:8000")
    logger.info("=" * 60)
    
    # Open browser automatically
    webbrowser.open("http://localhost:8000")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
