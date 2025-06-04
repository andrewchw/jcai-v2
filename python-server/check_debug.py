"""
Debug test script to check OAuth configuration and token status.
"""

import sys
from urllib.parse import quote

import requests


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_debug.py <user_id>")
        return

    user_id = sys.argv[1]
    print(f"Checking debug information for user: {user_id}")
    # Check OAuth config
    try:
        config_url = "http://localhost:8000/api/debug/oauth-config"
        print(f"Checking OAuth config at: {config_url}")
        config_response = requests.get(config_url)

        if config_response.status_code != 200:
            print(
                f"ERROR: Could not access OAuth config. Status code: {config_response.status_code}"
            )
            print(f"Response: {config_response.text}")
        else:
            config = config_response.json()
            print("\nOAuth Configuration:")
            print(f"Client ID: {config.get('client_id', 'Not available')}")
            print(f"Callback URL: {config.get('callback_url', 'Not available')}")
            print(f"Cloud ID from env: {config.get('cloud_id', 'Not available')}")
    except Exception as e:
        print(f"Error checking OAuth config: {str(e)}")
    # Check user token info
    try:
        debug_url = (
            f"http://localhost:8000/api/debug/user-token-info?user_id={quote(user_id)}"
        )
        print(f"Checking user token info at: {debug_url}")
        debug_response = requests.get(debug_url)

        if debug_response.status_code != 200:
            print(
                f"ERROR: Could not access user token info. Status code: {debug_response.status_code}"
            )
            print(f"Response: {debug_response.text}")
        else:
            debug_info = debug_response.json()
            print(f"\nToken Information for user {user_id}:")
            print(f"Token present: {debug_info.get('token', {}) != {}}")
            print(f"Cloud ID: {debug_info.get('cloud_id', 'Not available')}")
            print(f"Is connected: {debug_info.get('is_connected', False)}")

            # Display token details
            token = debug_info.get("token", {})
            if token:
                print("\nToken Details:")
                print(f"Access Token: {token.get('access_token', 'Not available')}")
                print(f"Refresh Token: {token.get('refresh_token', 'Not available')}")
                print(f"Expires At: {token.get('expires_at', 'Not available')}")
                print(f"Token Type: {token.get('token_type', 'Not available')}")
                print(f"Scope: {token.get('scope', 'Not available')}")
    except Exception as e:
        print(f"Error checking user token info: {str(e)}")


if __name__ == "__main__":
    main()
