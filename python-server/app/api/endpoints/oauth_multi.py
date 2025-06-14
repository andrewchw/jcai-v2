"""Multi-user OAuth endpoints for Jira Chatbot API.

These endpoints provide OAuth authentication for multiple users.
"""

import logging
import time
import traceback
import urllib.parse
import uuid
from datetime import datetime, timedelta
from typing import Optional

import requests
from app.core.config import settings
from app.core.database import get_db
from app.schemas.api_schemas import OAuthRequest, OAuthResponse, TokenResponse
from app.services.multi_user_jira_service import MultiUserJiraService
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/oauth/v2",
    tags=["oauth-multiuser"],
    responses={404: {"description": "Not found"}},
)


@router.get("/login", response_model=OAuthResponse)
async def login(
    request: Request, user_data: OAuthRequest = Depends(), db: Session = Depends(get_db)
):
    """
    Start OAuth login process for a user.

    If user_id is provided, it will be used as the identifier.
    If email or jira_account_id is provided, they will be used to look up or create a user.
    If no identifier is provided, a temporary user ID will be generated.
    """
    try:
        service = MultiUserJiraService(db)

        # Determine user ID
        user_id = user_data.user_id

        # If no user_id provided, try to find by email or Jira ID
        if not user_id:
            user_data_dict = {}

            if user_data.email:
                user_data_dict["email"] = user_data.email

            if user_data.jira_account_id:
                user_data_dict["jira_account_id"] = user_data.jira_account_id

            # If we have some user data, try to get/create user
            if user_data_dict:
                user_id = service.get_or_create_user(user_data_dict)
            else:
                # Generate temporary user ID
                user_id = f"temp-{str(uuid.uuid4())}"  # Generate real authorization URL using environment variables
        from app.core.config import settings

        # Get OAuth configuration
        client_id = settings.JIRA_OAUTH_CLIENT_ID
        redirect_uri = settings.JIRA_OAUTH_CALLBACK_URL

        # Include user_id in the state parameter for security
        state = f"user_id:{user_id}"

        if client_id and redirect_uri:  # Get scope from settings if available
            scope = getattr(
                settings,
                "ATLASSIAN_OAUTH_SCOPE",
                "read:jira-work write:jira-work offline_access",
            )

            # Create a real OAuth authorization URL
            auth_url = f"https://auth.atlassian.com/authorize?audience=api.atlassian.com&client_id={client_id}&scope={urllib.parse.quote(scope)}&redirect_uri={redirect_uri}&state={state}&response_type=code&prompt=consent"
            callback_url = auth_url
            logger.info(f"Generated OAuth URL for user {user_id}: {auth_url}")
        else:
            # Fall back to test mode if OAuth credentials aren't configured
            logger.warning(
                f"OAuth credentials not configured, using test mode for user {user_id}"
            )
            callback_url = (
                f"/callback?setup_example=true&success=true&user_id={user_id}"
            )

        # Determine if this is an API request or browser request
        if (
            "Accept" in request.headers
            and "application/json" in request.headers["Accept"]
            and "text/html" not in request.headers["Accept"]
        ):
            # API request - return JSON
            return OAuthResponse(
                success=True,
                message="Redirecting to authorization page",
                redirect_url=callback_url,
            )

        # Browser request - redirect to callback
        return RedirectResponse(url=callback_url)

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return OAuthResponse(
            success=False,
            message=f"Failed to start login process: {str(e)}",
            redirect_url=None,
        )


@router.get("/callback")
async def callback(
    request: Request,
    user_id: Optional[str] = None,
    code: Optional[str] = None,
    state: Optional[str] = None,
    setup_example: bool = False,
    success: bool = False,
    db: Session = Depends(get_db),
):
    """
    Handle OAuth callback from authorization server with multi-user support.

    Args:
        request: The request object
        user_id: The user ID to associate with the token
        code: The authorization code (for real OAuth)
        state: The state passed to the authorization server
        setup_example: Whether to set up a test token
    success: Whether the authorization was successful
    """
    # Extract user_id from state if present
    if state and state.startswith("user_id:"):
        extracted_user_id = state.split("user_id:")[1]
        if not user_id or not isinstance(
            user_id, str
        ):  # Only use if no direct user_id provided or if it's not a string
            user_id = extracted_user_id
            logger.info(
                f"Extracted user_id from state: {user_id}"
            )  # Make sure user_id is a string
    if user_id and not isinstance(user_id, str):
        logger.warning(f"user_id is not a string: {type(user_id)}. Trying to convert.")
        try:
            user_id = str(user_id)
        except (ValueError, TypeError) as e:
            user_id = None
            logger.error(f"Could not convert user_id to string: {e}")

    # Log the callback request details
    logger.info(
        f"OAuth callback received: user_id={user_id}, setup_example={setup_example}, "
        f"success={success}, code={'present' if code else 'missing'}"
    )

    try:
        # Initialize with failure by default
        auth_success = success or False
        message = "Authentication failed"

        # Require a user ID
        if not user_id:
            message = "No user ID provided"
            auth_success = False
        else:
            service = MultiUserJiraService(db)

            # Handle real OAuth code exchange
            if code and not setup_example:
                try:
                    # Exchange code for token
                    client_id = settings.JIRA_OAUTH_CLIENT_ID
                    client_secret = settings.JIRA_OAUTH_CLIENT_SECRET
                    redirect_uri = settings.JIRA_OAUTH_CALLBACK_URL

                    # Make token request
                    token_url = "https://auth.atlassian.com/oauth/token"
                    token_data = {
                        "grant_type": "authorization_code",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    }

                    logger.info(f"Exchanging code for token for user {user_id}")
                    token_response = requests.post(token_url, json=token_data)

                    if token_response.status_code == 200:  # Process token response
                        token = token_response.json()

                        # Add expires_at field (access_token typically expires in 1 hour)
                        expires_in = token.get("expires_in", 3600)  # Default to 1 hour
                        token["expires_at"] = datetime.now().timestamp() + expires_in
                        token["created_at"] = datetime.now().timestamp()

                        # Ensure user record exists before saving token
                        try:
                            # Create or update user record with the specific user_id
                            user_data = {
                                "id": user_id,  # Use the exact user_id as the primary key
                                "display_name": f"User {user_id[:8]}",  # Use partial user_id as display name
                                "is_active": True,
                            }
                            service.get_or_create_user(user_data)
                            logger.info(f"Ensured user record exists for {user_id}")
                        except Exception as user_creation_error:
                            logger.warning(
                                f"Failed to create user record for {user_id}: {str(user_creation_error)}"
                            )
                            # Continue anyway - token saving might still work

                        # Save the token
                        if service.save_token_for_user(user_id, token):
                            auth_success = True
                            message = "Authentication successful"
                            logger.info(
                                f"Obtained and saved real OAuth token for user {user_id}"
                            )

                            # Get Jira Cloud ID (in background)
                            try:
                                jira_service = service.get_jira_service(user_id)
                                if jira_service:
                                    logger.info(
                                        "Retrieving Jira Cloud ID from accessible resources..."
                                    )
                                    jira_service.get_cloud_id()
                            except Exception as cloud_id_err:
                                logger.error(
                                    f"Error retrieving Jira Cloud ID: {str(cloud_id_err)}"
                                )
                        else:
                            auth_success = False
                            message = "Failed to save token"
                            logger.error(f"Failed to save token for user {user_id}")
                    else:
                        # Token exchange failed
                        error_details = (
                            token_response.json()
                            if token_response.content
                            else {"error": "Unknown error"}
                        )
                        auth_success = False
                        message = f"Failed to obtain token: {error_details.get('error', 'Unknown error')}"
                        logger.error(
                            f"Token exchange failed: {token_response.status_code} - {error_details}"
                        )
                except Exception as token_ex:
                    logger.error(f"Error during token exchange: {str(token_ex)}")
                    auth_success = False
                    message = f"Error during token exchange: {str(token_ex)}"

            # Handle test/example setup as fallback
            elif setup_example:
                logger.info("Using test token for authentication")
                # Create a test token
                expires_at = datetime.now() + timedelta(hours=1)

                token = {
                    "access_token": f"test_access_token_{int(time.time())}",
                    "refresh_token": f"test_refresh_token_{int(time.time())}",
                    "token_type": "Bearer",
                    "expires_at": expires_at.timestamp(),
                    "expires_in": 3600,  # 1 hour
                    "created_at": datetime.now().timestamp(),
                }

                # Ensure user record exists before saving token
                try:
                    # Create or update user record with the specific user_id
                    user_data = {
                        "id": user_id,  # Use the exact user_id as the primary key
                        "display_name": f"User {user_id[:8]}",  # Use partial user_id as display name
                        "is_active": True,
                    }
                    service.get_or_create_user(user_data)
                    logger.info(f"Ensured user record exists for {user_id}")
                except Exception as user_creation_error:
                    logger.warning(
                        f"Failed to create user record for {user_id}: {str(user_creation_error)}"
                    )
                    # Continue anyway - token saving might still work

                # Save the token for this user
                if service.save_token_for_user(user_id, token):
                    auth_success = True
                    message = "Authentication successful (Test Mode)"
                    logger.info(f"Created test token for user {user_id}")
                else:
                    auth_success = False
                    message = "Failed to save test token"
                    logger.error(f"Failed to save test token for user {user_id}")

            # Handle case where no valid method was provided
            else:
                message = "No valid authentication method provided"

        # Create HTML response same as in original implementation...
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
                    color: {"#0052CC" if auth_success else "#DE350B"};
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
                    {"✅" if auth_success else "❌"}
                </div>
                <h1>{"Authentication Successful" if auth_success else "Authentication Failed"}</h1>
                <p>{message}</p>
                <p>This window will close automatically in a few seconds.</p>
            </div>
        </body>
        </html>        """

        # Log the final auth status
        logger.info(
            f"OAuth authentication completed: user_id={user_id}, success={auth_success}, message={message}"
        )

        # Handle API vs browser request
        if (
            "Accept" in request.headers
            and "application/json" in request.headers["Accept"]
            and "text/html" not in request.headers["Accept"]
        ):
            # API request - return JSON
            return {"success": auth_success, "message": message, "user_id": user_id}
        # Browser request - return HTML with redirect for success
        if auth_success:
            # Make sure the URL will have the success=true parameter to signal the extension
            success_url = f"/callback?success=true&user_id={user_id}"
            if setup_example:
                success_url += "&setup_example=true"

            response_html = (
                html_content
                + f"""
            <script>
                // Notify extension of success by updating URL parameter
                window.history.replaceState(null, "", "{success_url}");
                  // If this was opened from our extension, communicate success back to it
                if (window.opener) {{
                    try {{
                        window.opener.postMessage({{
                            type: "oauth-success",
                            user_id: "{user_id}"
                        }}, "*");
                    }} catch (e) {{
                        console.error("Could not send message to opener:", e);
                    }}
                }}
            </script>
            """
            )
            return HTMLResponse(response_html)
        else:
            return HTMLResponse(html_content)

    except Exception as e:
        logger.error(f"Error during OAuth callback: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

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


@router.get("/token/status", response_model=TokenResponse)
async def get_token_status(user_id: str, db: Session = Depends(get_db)):
    """Get the current OAuth token status for a user."""
    try:
        service = MultiUserJiraService(db)
        token = service.get_token_for_user(user_id)
        if not token:
            return TokenResponse(status="error")

        # Calculate expiration information
        expires_at = token.get("expires_at")
        current_time = datetime.now().timestamp()
        time_remaining = expires_at - current_time if expires_at else 0

        if time_remaining > 0:
            status = "active"
        else:
            status = "expired"

        return TokenResponse(
            status=status,
            expires_in_seconds=int(time_remaining) if time_remaining > 0 else 0,
            expires_at=(
                datetime.fromtimestamp(expires_at).isoformat() if expires_at else None
            ),
            provider="jira",
            last_used=(
                datetime.fromtimestamp(
                    token.get("last_used_at", current_time)
                ).isoformat()
                if token.get("last_used_at")
                else None
            ),
        )

    except Exception as e:
        logger.error(f"Exception type during get_token_status: {type(e)}")
        logger.error(f"Exception args during get_token_status: {e.args}")
        logger.error(f"Error getting token status: {str(e)}")
        return TokenResponse(status="error")


@router.get("/logout")
async def logout(user_id: str, db: Session = Depends(get_db)):
    """Logout and invalidate OAuth token for a user."""
    try:
        service = MultiUserJiraService(db)
        success = service.logout_user(user_id)

        if success:
            return {"success": True, "message": "Successfully logged out"}
        else:
            return {"success": False, "message": "No token found for this user"}

    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to logout: {str(e)}")


@router.post("/logout")
async def logout_post(user_id: str, db: Session = Depends(get_db)):
    """Logout and invalidate OAuth token for a user via POST request."""
    # This simply calls the same implementation as the GET endpoint
    return await logout(user_id=user_id, db=db)


@router.post("/remember-me/enable")
async def enable_remember_me(
    user_id: str, extended_duration_days: int = 7, db: Session = Depends(get_db)
):
    """Enable 'Remember Me' feature for a user with extended session duration."""
    try:
        service = MultiUserJiraService(db)

        # Get the user from database
        user = service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update user preferences
        user.remember_me_enabled = True
        user.extended_session_duration_days = extended_duration_days
        user.last_remember_me_login = datetime.now()

        # Get current token and enable extended session
        token_record = service.get_token_record_for_user(user_id)
        if token_record:
            token_record.enable_extended_session(extended_duration_days)
            db.commit()

            logger.info(
                f"Enabled 'Remember Me' for user {user_id} with {extended_duration_days} days extension"
            )

            return {
                "success": True,
                "message": f"Remember Me enabled for {extended_duration_days} days",
                "extended_expires_at": token_record.extended_expires_at,
                "original_expires_at": token_record.original_expires_at,
            }
        else:
            # Just update user preferences even if no active token
            db.commit()
            return {
                "success": True,
                "message": "Remember Me preferences saved (will apply to next login)",
                "extended_duration_days": extended_duration_days,
            }

    except Exception as e:
        logger.error(f"Error enabling Remember Me: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to enable Remember Me: {str(e)}"
        )


@router.post("/remember-me/disable")
async def disable_remember_me(user_id: str, db: Session = Depends(get_db)):
    """Disable 'Remember Me' feature for a user."""
    try:
        service = MultiUserJiraService(db)

        # Get the user from database
        user = service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update user preferences
        user.remember_me_enabled = False
        user.last_remember_me_login = None

        # Get current token and disable extended session
        token_record = service.get_token_record_for_user(user_id)
        if token_record:
            token_record.disable_extended_session()
            db.commit()

            logger.info(f"Disabled 'Remember Me' for user {user_id}")

            return {
                "success": True,
                "message": "Remember Me disabled",
                "expires_at": token_record.expires_at,
            }
        else:
            # Just update user preferences
            db.commit()
            return {"success": True, "message": "Remember Me preferences updated"}

    except Exception as e:
        logger.error(f"Error disabling Remember Me: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to disable Remember Me: {str(e)}"
        )


@router.get("/remember-me/status")
async def get_remember_me_status(user_id: str, db: Session = Depends(get_db)):
    """Get current 'Remember Me' status for a user."""
    try:
        service = MultiUserJiraService(db)

        # Get the user from database
        user = service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get current token status
        token_record = service.get_token_record_for_user(user_id)
        token_status = None
        if token_record:
            token_status = {
                "is_extended_session": token_record.is_extended_session,
                "extended_expires_at": token_record.extended_expires_at,
                "original_expires_at": token_record.original_expires_at,
                "effective_expires_at": token_record.effective_expires_at,
                "is_expired": token_record.is_expired,
            }

        return {
            "remember_me_enabled": user.remember_me_enabled,
            "extended_session_duration_days": user.extended_session_duration_days,
            "last_remember_me_login": (
                user.last_remember_me_login.isoformat()
                if user.last_remember_me_login
                else None
            ),
            "token_status": token_status,
        }

    except Exception as e:
        logger.error(f"Error getting Remember Me status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get Remember Me status: {str(e)}"
        )
