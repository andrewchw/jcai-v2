#!/usr/bin/env python3
"""
OAuth Token Checker

This script checks if an OAuth 2.0 token exists, displays its information,
and validates if it's still active.

It provides details about the token, including:
- Token existence and location
- Expiration time and validity
- Token contents (masked for security)
- Accessible Jira resources
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default token file location
TOKEN_FILE = os.getenv("TOKEN_FILE", "oauth_token.json")
RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


def load_token():
    """Load OAuth token from file"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                token = json.load(f)
                logger.info(f"Token loaded from {TOKEN_FILE}")
                return token
    except Exception as e:
        logger.error(f"Could not load token: {str(e)}")

    logger.warning(f"No token found at {TOKEN_FILE}")
    return None


def check_token_expiry(token):
    """Check if the token is expired and provide detailed information"""
    if not token:
        logger.warning("No token provided for expiry check")
        return None

    if "expires_at" in token:
        expires_at = token["expires_at"]
        current_time = datetime.now().timestamp()

        # Calculate time remaining
        time_remaining = expires_at - current_time

        if time_remaining <= 0:
            logger.warning("Token is expired!")
            expired_for = timedelta(seconds=abs(time_remaining))
            logger.warning(f"Token expired {expired_for} ago")
            return False
        else:
            # Format time remaining for better readability
            remaining_td = timedelta(seconds=time_remaining)
            hours, remainder = divmod(int(time_remaining), 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours > 0:
                logger.info(f"Token valid for {hours}h {minutes}m {seconds}s more")
            else:
                logger.info(f"Token valid for {minutes}m {seconds}s more")

            # Warn if token is about to expire
            if time_remaining < 300:  # Less than 5 minutes
                logger.warning("Token is about to expire soon!")

            return True
    else:
        logger.warning("Token does not have an expiration timestamp")
        return None


def get_accessible_resources(token):
    """Get accessible Jira Cloud instances using the token"""
    import requests

    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            "https://api.atlassian.com/oauth/token/accessible-resources",
            headers=headers,
        )

        if response.status_code == 200:
            resources = response.json()
            return resources
        else:
            logger.error(
                f"Error accessing resources: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        logger.error(f"Error getting accessible resources: {str(e)}")
        return None


def mask_token(token_value):
    """Masks most of a token value for security"""
    if not token_value:
        return None

    if len(token_value) <= 15:
        return token_value[:5] + "..." if len(token_value) > 5 else token_value
    else:
        return token_value[:10] + "..." + token_value[-5:]


def format_time_remaining(seconds):
    """Format seconds into a human-readable time string"""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def main():
    """Main function to test the OAuth token"""
    print("\n=== OAuth Token Status ===\n")

    # Load token
    token = load_token()

    if not token:
        print("❌ No OAuth token found")
        print(f"   Expected location: {os.path.abspath(TOKEN_FILE)}")
        print("\nPlease run the OAuth flow to obtain a token:")
        print("   python jira_oauth2_example.py")
        print("   Then visit http://localhost:8000/login")
        return
    # Check token expiry
    is_valid = check_token_expiry(token)

    # Display token information
    print(f"✅ OAuth token found: {os.path.abspath(TOKEN_FILE)}")
    # Show token details
    print("\n--- Token Details ---")
    print(f"Access Token: {mask_token(token.get('access_token'))}")
    print(f"Token Type: {token.get('token_type', 'Unknown')}")
    # Check for refresh token
    if "refresh_token" in token:
        print(f"Refresh Token: {mask_token(token.get('refresh_token'))}")
        print("♻️ Auto-renewal: ✅ Enabled (token can be refreshed)")
    else:
        print("♻️ Auto-renewal: ❌ Disabled (no refresh token)")
        print("   To enable refresh tokens:")
        print("   1. Configure your app in the Atlassian Developer Console")
        print("   2. Enable 'Refresh Token' option in Authorization settings")
        print("   3. Re-authenticate to get a new token")

    # Show expiration information
    if "expires_at" in token:
        expires_at = token["expires_at"]
        current_time = datetime.now().timestamp()
        time_remaining = expires_at - current_time

        if time_remaining <= 0:
            print("⏱️ Status: ❌ Expired")
            expired_for = format_time_remaining(abs(time_remaining))
            print(f"   (Expired {expired_for} ago)")
        else:
            print("⏱️ Status: ✅ Valid")
            valid_for = format_time_remaining(time_remaining)
            print(f"   (Expires in {valid_for})")
    else:
        print("⏱️ Expiration: Unknown")

    # Display scopes
    scopes = token.get("scope", [])
    if isinstance(scopes, str):
        scopes = scopes.split()

    print("\nScopes:")
    for scope in scopes:
        print(f"   ✓ {scope}")

    # Test token with API call
    print("\n--- Accessible Jira Sites ---")
    resources = get_accessible_resources(token)

    if not resources:
        print("❌ Could not access Jira resources with this token")
        print("   Token might be expired or invalid")
        print("\nTry refreshing your token:")
        print("   python jira_oauth2_example.py")
        return

    # Print resources
    print(f"✅ Successfully accessed {len(resources)} Jira Cloud instance(s)")

    for i, resource in enumerate(resources):
        print(f"\n{i+1}. {resource.get('name', 'Unknown')}")
        print(f"   ID: {resource.get('id', 'Unknown')}")
        print(f"   URL: https://{resource.get('url', 'Unknown')}")
        if "avatarUrl" in resource:
            print(f"   Avatar URL: {resource.get('avatarUrl')}")

    print("\n✅ OAuth token is valid and working correctly!")
    print("   You can now use this token with the Atlassian Python API")


if __name__ == "__main__":
    main()
