#!/usr/bin/env python3
"""
Enhanced OAuth 2.0 Example for Jira API with improved error handling.
"""
import json
import logging
import os
import secrets
import sys
import time
import traceback
import webbrowser
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from requests_oauthlib import OAuth2Session
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# OAuth 2.0 Configuration
CLIENT_ID = os.environ.get("JIRA_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("JIRA_OAUTH_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("JIRA_OAUTH_CALLBACK_URL")
AUTH_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
SCOPE = [
    "read:jira-user",
    "read:jira-work",
    "write:jira-work",
    "manage:jira-project",
    "manage:jira-configuration",
    "offline_access",  # Required for refresh tokens
]
AUDIENCE = "api.atlassian.com"
TOKEN_FILE = "oauth_token.json"

# FastAPI App
app = FastAPI()

# OAuth session object (will be initialized in login route)
jira_oauth = None

# For session tracking
state = secrets.token_urlsafe(15)

def delete_token_file():
    """Delete the token file if it exists."""
    try:
        token_path = Path(TOKEN_FILE)
        if token_path.exists():
            token_path.unlink()
            logger.info(f"Deleted existing token file: {TOKEN_FILE}")
    except Exception as e:
        logger.error(f"Error deleting token file: {e}")

def save_token(token):
    """Save the token to a file."""
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(token, f)
        logger.info(f"Token saved to {TOKEN_FILE}")
        
        # Print token information
        logger.info("Token details:")
        logger.info(f"  Access token expires in: {token.get('expires_in')} seconds")
        logger.info(f"  Refresh token provided: {'refresh_token' in token}")
        
        # Also make the file readable for debugging
        with open(f"{TOKEN_FILE}.readable", "w") as f:
            json.dump(token, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save token: {e}")
        traceback.print_exc()

def load_token() -> Optional[Dict]:
    """Load the token from a file."""
    try:
        if not Path(TOKEN_FILE).exists():
            logger.warning(f"Token file {TOKEN_FILE} does not exist")
            return None
            
        with open(TOKEN_FILE, "r") as f:
            token = json.load(f)
        logger.info(f"Token loaded from {TOKEN_FILE}")
        return token
    except Exception as e:
        logger.error(f"Failed to load token: {e}")
        return None

def token_updater(token):
    """Callback to save the refreshed token."""
    logger.info("Token refreshed, saving updated token...")
    save_token(token)

def make_oauth_session(token=None):
    """Create an OAuth 2.0 session."""
    extra = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE,
    }
    
    session = OAuth2Session(
        CLIENT_ID,
        scope=SCOPE,
        redirect_uri=REDIRECT_URI,
        token=token,
        auto_refresh_url=TOKEN_URL,
        auto_refresh_kwargs=extra,
        token_updater=token_updater,
    )
    return session

@app.get("/")
async def homepage():
    """Homepage with link to login."""
    html_content = """
    <html>
        <head>
            <title>Jira OAuth2 Example</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                    color: #333;
                }
                h1 {
                    color: #0052CC;
                }
                a {
                    display: inline-block;
                    background-color: #0052CC;
                    color: white;
                    padding: 10px 15px;
                    text-decoration: none;
                    border-radius: 3px;
                    font-weight: bold;
                    margin-top: 20px;
                }
                a:hover {
                    background-color: #0747A6;
                }
                pre {
                    background-color: #f4f4f4;
                    padding: 10px;
                    border-radius: 5px;
                    overflow: auto;
                }
            </style>
        </head>
        <body>
            <h1>Jira OAuth2 Example</h1>
            <p>This example demonstrates the OAuth 2.0 flow with Jira.</p>
            <p>Click the button below to begin the OAuth 2.0 flow.</p>
            <a href="/login">Start OAuth Flow</a>
            
            <p>Make sure your OAuth 2.0 configuration is set up correctly in your .env file:</p>
            <pre>
JIRA_OAUTH_CLIENT_ID=your-client-id
JIRA_OAUTH_CLIENT_SECRET=your-client-secret
JIRA_OAUTH_CALLBACK_URL=http://localhost:8000/callback
            </pre>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/login")
async def login():
    """Start the OAuth 2.0 flow."""
    global jira_oauth
    
    # Delete any existing token file to start fresh
    delete_token_file()
    
    # Create a fresh OAuth session
    jira_oauth = make_oauth_session()
    
    # Generate authorization URL
    params = {
        "audience": AUDIENCE,
        "state": state,
        "response_type": "code",
        "prompt": "consent",  # Always ask for consent to ensure we get a fresh token
    }
    authorization_url, _ = jira_oauth.authorization_url(AUTH_URL, **params)
    
    logger.info(f"Authorization URL: {authorization_url}")
    
    # Open the URL in a browser automatically
    try:
        webbrowser.open(authorization_url)
        logger.info("Opened authorization URL in browser")
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
    
    return RedirectResponse(authorization_url)

@app.get("/callback")
async def callback(request: Request):
    """Handle the OAuth 2.0 callback."""
    global jira_oauth
    
    # Extract query parameters
    params = dict(request.query_params)
    logger.info(f"Received callback with parameters: {params}")
    
    # Check for errors in the callback
    if "error" in params:
        error_msg = f"Error in OAuth callback: {params['error']}"
        if "error_description" in params:
            error_msg += f" - {params['error_description']}"
        logger.error(error_msg)
        return HTMLResponse(f"<h1>OAuth Error</h1><p>{error_msg}</p>")
    
    # Validate state to prevent CSRF
    if "state" not in params or params["state"] != state:
        logger.error(f"State mismatch. Expected: {state}, Got: {params.get('state')}")
        return HTMLResponse("<h1>State Validation Failed</h1><p>Invalid state parameter. This could be a CSRF attempt.</p>")
    
    # Check for authorization code
    if "code" not in params:
        logger.error("No authorization code received")
        return HTMLResponse("<h1>No Code</h1><p>No authorization code received from Jira.</p>")
    
    try:
        logger.info("OAuth token obtained successfully")
        code = params["code"]
        
        # Exchange the code for a token
        logger.info("Exchanging authorization code for token...")
        token = jira_oauth.fetch_token(
            TOKEN_URL,
            code=code,
            client_secret=CLIENT_SECRET,
            include_client_id=True,
        )
        
        # Save the token
        save_token(token)
        
        # Try to use the token to get accessible resources
        try:
            logger.info("Testing token by fetching accessible resources...")
            response = jira_oauth.get(
                "https://api.atlassian.com/oauth/token/accessible-resources"
            )
            resources = response.json()
            logger.info(f"Successfully retrieved {len(resources)} accessible resources")
            
            # Get the Cloud ID of the first resource (Jira site)
            if resources:
                cloud_id = resources[0]["id"]
                logger.info(f"Jira Cloud ID: {cloud_id}")
                
                # Save the cloud ID to a separate file for easy access
                with open("cloud_id.txt", "w") as f:
                    f.write(cloud_id)
                logger.info(f"Cloud ID saved to cloud_id.txt")
                
                # Update the .env file with the Cloud ID if ATLASSIAN_OAUTH_CLOUD_ID is present
                try:
                    env_path = Path(".env")
                    if env_path.exists():
                        with open(env_path, "r") as f:
                            env_lines = f.readlines()
                        
                        updated = False
                        for i, line in enumerate(env_lines):
                            if line.startswith("ATLASSIAN_OAUTH_CLOUD_ID="):
                                env_lines[i] = f"ATLASSIAN_OAUTH_CLOUD_ID={cloud_id}\n"
                                updated = True
                                break
                        
                        if not updated:
                            env_lines.append(f"ATLASSIAN_OAUTH_CLOUD_ID={cloud_id}\n")
                        
                        with open(env_path, "w") as f:
                            f.writelines(env_lines)
                        
                        logger.info(f"Updated .env file with Cloud ID: {cloud_id}")
                except Exception as e:
                    logger.error(f"Error updating .env file with Cloud ID: {e}")
        
        except Exception as e:
            logger.error(f"Error testing token: {e}")
        
        html_response = """
        <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        max-width: 800px;
                        margin: 0 auto;
                        color: #333;
                    }
                    h1 {
                        color: #0B875B;
                    }
                    .success-box {
                        background-color: #E3FCEF;
                        border: 1px solid #0B875B;
                        padding: 20px;
                        border-radius: 5px;
                        margin-top: 20px;
                    }
                    pre {
                        background-color: #f4f4f4;
                        padding: 10px;
                        border-radius: 5px;
                        overflow: auto;
                    }
                    code {
                        font-family: monospace;
                    }
                    .next-steps {
                        margin-top: 30px;
                        padding: 20px;
                        background-color: #DEEBFF;
                        border-radius: 5px;
                    }
                </style>
            </head>
            <body>
                <h1>Authentication Successful</h1>
                <div class="success-box">
                    <p>✅ Successfully authenticated with Jira!</p>
                    <p>✅ Token has been saved to <code>oauth_token.json</code></p>
        """
        
        if 'resources' in locals() and len(resources) > 0:
            html_response += f"""
                    <p>✅ Retrieved Jira Cloud ID: <code>{cloud_id}</code></p>
                    <p>✅ Cloud ID has been saved to <code>cloud_id.txt</code></p>
            """
            
        html_response += """
                </div>
                <div class="next-steps">
                    <h2>Next Steps</h2>
                    <p>You can now use the token to make authenticated requests to the Jira API.</p>
                    <p>To run your server:</p>
                    <pre>python run.py</pre>
                </div>
                <p>You can close this window now.</p>
            </body>
        </html>
        """
        
        return HTMLResponse(html_response)
    
    except Exception as e:
        error_msg = f"Error completing OAuth flow: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        html_response = f"""
        <html>
            <head>
                <title>Authentication Failed</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        max-width: 800px;
                        margin: 0 auto;
                        color: #333;
                    }}
                    h1 {{
                        color: #DE350B;
                    }}
                    .error-box {{
                        background-color: #FFEBE6;
                        border: 1px solid #DE350B;
                        padding: 20px;
                        border-radius: 5px;
                        margin-top: 20px;
                    }}
                    pre {{
                        background-color: #f4f4f4;
                        padding: 10px;
                        border-radius: 5px;
                        overflow: auto;
                    }}
                    .troubleshooting {{
                        margin-top: 30px;
                        padding: 20px;
                        background-color: #f4f4f4;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <h1>Authentication Failed</h1>
                <div class="error-box">
                    <p>❌ Failed to complete OAuth flow.</p>
                    <p><strong>Error:</strong> {str(e)}</p>
                </div>
                <div class="troubleshooting">
                    <h2>Troubleshooting</h2>
                    <p>Common issues:</p>
                    <ul>
                        <li>Authorization code expired or already used</li>
                        <li>Client ID or Secret mismatch</li>
                        <li>Callback URL doesn't match what's registered in Atlassian</li>
                        <li>Insufficient permissions for the Atlassian account</li>
                    </ul>
                    <p>Please try again by clicking <a href="/login">here</a>.</p>
                </div>
            </body>
        </html>
        """
        
        return HTMLResponse(html_response)

def main():
    """Main entry point."""
    logger.info("Starting enhanced OAuth2 example server...")
    logger.info(f"Callback URL is set to: {REDIRECT_URI}")
    logger.info("Please make sure this matches the Callback URL in your Atlassian OAuth 2.0 application settings")
    
    # Check if the required environment variables are set
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        logger.error("Missing required environment variables. Please set JIRA_OAUTH_CLIENT_ID, JIRA_OAUTH_CLIENT_SECRET, and JIRA_OAUTH_CALLBACK_URL in your .env file.")
        sys.exit(1)
        
    logger.info("Attempting to start server on http://localhost:8000")
    logger.info("Navigate to http://localhost:8000 to begin the OAuth flow")
    
    # Run the app
    try:
        uvicorn.run(app, host="localhost", port=8000)
    except OSError as e:
        if "Address already in use" in str(e) or "Only one usage of each socket address" in str(e):
            logger.error(f"Port 8000 is already in use. Please stop any other processes using port 8000 and try again.")
            logger.info("You can use the following commands to find and stop processes using port 8000:")
            logger.info("Windows: netstat -ano | findstr :8000")
            logger.info("         taskkill /F /PID <PID>")
            logger.info("macOS/Linux: lsof -i :8000")
            logger.info("             kill -9 <PID>")
        else:
            logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
