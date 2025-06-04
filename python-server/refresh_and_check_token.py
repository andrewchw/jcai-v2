#!/usr/bin/env python3
"""
OAuth Token Refresher and Checker

This script checks if an OAuth 2.0 token exists and is still valid.
If the token is expired or about to expire, it will automatically
refresh it using the same logic as the FastAPI application.

It provides details about the token, including:
- Token existence and location
- Expiration time and validity (before and after refresh)
- Accessible Jira resources validation
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# OAuth2 settings from environment variables
TOKEN_FILE = os.getenv("TOKEN_FILE", "oauth_token.json")
CLIENT_ID = os.getenv("JIRA_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("JIRA_OAUTH_CLIENT_SECRET")
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
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


def save_token(token):
    """Save OAuth token to file"""
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(token, f)
        logger.info(f"Token saved to {TOKEN_FILE}")
        return True
    except Exception as e:
        logger.error(f"Could not save token: {str(e)}")
        return False


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


def refresh_token(token):
    """Refresh the OAuth 2.0 token if it's expired"""
    try:
        # Create a new OAuth2 session
        oauth = OAuth2Session(CLIENT_ID, token=token)

        # Check if token is expired or about to expire (within 60 seconds)
        if "expires_at" in token:
            expires_at = token["expires_at"]
            current_time = datetime.now().timestamp()
            time_remaining = expires_at - current_time

            if (
                time_remaining <= 60
            ):  # Within 60 seconds of expiration or already expired
                if time_remaining <= 0:
                    print(
                        f"\n⚠️ Token EXPIRED {timedelta(seconds=int(abs(time_remaining)))} ago"
                    )
                else:
                    print(
                        f"\n⚠️ Token will expire in {timedelta(seconds=int(time_remaining))}"
                    )

                print("🔄 Refreshing token...")

                # Refresh the token
                new_token = oauth.refresh_token(
                    TOKEN_URL,
                    refresh_token=token["refresh_token"],
                    client_id=CLIENT_ID,
                    client_secret=CLIENT_SECRET,
                )

                # Calculate new expiration
                if "expires_at" in new_token:
                    new_expires_at = new_token["expires_at"]
                    new_expiry = datetime.fromtimestamp(new_expires_at)
                    print(
                        f"✅ Token refreshed successfully! New expiration: {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                # Save the new token
                save_token(new_token)
                return new_token
            else:
                print(
                    f"\n✅ Token is still valid for {timedelta(seconds=int(time_remaining))}"
                )
                print("   No refresh needed")

        return token
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        print(f"\n❌ Error refreshing token: {str(e)}")
        return token  # Return original token on error


def get_accessible_resources(token):
    """Get accessible Jira Cloud instances using the token"""
    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Accept": "application/json",
    }

    try:
        response = requests.get(RESOURCES_URL, headers=headers)

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


def main():
    """Main function to check and refresh the OAuth token"""
    print("\n=== OAuth Token Status & Refresh ===\n")

    # Load token
    token = load_token()

    if not token:
        print("❌ No OAuth token found")
        print(f"   Expected location: {os.path.abspath(TOKEN_FILE)}")
        print("\nPlease run the OAuth flow to obtain a token:")
        print("   python jira_oauth2_example.py")
        print("   Then visit http://localhost:8000/login")
        return

    # Print original token info
    print("📃 Original token information:")
    print(f"   Location: {os.path.abspath(TOKEN_FILE)}")
    print(f"   Access Token: {mask_token(token.get('access_token'))}")
    print(f"   Token Type: {token.get('token_type', 'Unknown')}")

    # Check for refresh token
    if "refresh_token" in token:
        print(f"   Refresh Token: {mask_token(token.get('refresh_token'))}")
        print("   ♻️ Auto-renewal: ✅ Enabled")
    else:
        print("   ♻️ Auto-renewal: ❌ Disabled (no refresh token)")
        print("   ⛔ Cannot refresh this token. Please re-authenticate.")
        return

    # Check expiration of original token
    original_expiry = None
    if "expires_at" in token:
        expires_at = token["expires_at"]
        current_time = datetime.now().timestamp()
        time_remaining = expires_at - current_time

        if time_remaining <= 0:
            expired_for = timedelta(seconds=int(abs(time_remaining)))
            print(f"   ⏱️ Status: ❌ Expired ({expired_for} ago)")
        else:
            time_left = timedelta(seconds=int(time_remaining))
            print(f"   ⏱️ Status: ✅ Valid (expires in {time_left})")
    else:
        print("   ⏱️ Expiration: Unknown")

    # Refresh token if needed
    refreshed_token = refresh_token(token)

    # Verify the refreshed token with an API call
    print("\n=== Testing Token with API Call ===")
    print("🔍 Testing access to Jira resources...")

    resources = get_accessible_resources(refreshed_token)
    if not resources:
        print("\n❌ Could not access Jira resources with this token")
        print("   Token might be invalid or not have sufficient permissions")
        print("\nTry obtaining a fresh token:")
        print("   python logout_oauth_token.py")
        print("   python jira_oauth2_example.py")
        return

    # Print resources
    print(f"\n✅ Successfully accessed {len(resources)} Jira Cloud instance(s)")

    for i, resource in enumerate(resources):
        print(f"\n{i+1}. {resource.get('name', 'Unknown')}")
        print(f"   ID: {resource.get('id', 'Unknown')}")
        print(f"   URL: https://{resource.get('url', 'Unknown')}")

    print("\n✅ Token is valid and working correctly!")


if __name__ == "__main__":
    main()
