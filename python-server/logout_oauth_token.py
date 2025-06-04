#!/usr/bin/env python3
"""
OAuth Token Logout Script

This script deletes the stored OAuth token and allows you to re-authenticate
to get a new token with a refresh token.
"""

import logging
import os
import sys

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


def main():
    """Main function to delete the OAuth token"""
    print("\n=== OAuth Token Logout ===\n")

    if os.path.exists(TOKEN_FILE):
        try:
            # Delete the token file
            os.remove(TOKEN_FILE)
            print(f"✅ Successfully deleted OAuth token: {os.path.abspath(TOKEN_FILE)}")
            print("\nYou can now login again to get a new token with a refresh token:")
            print("   1. Run the OAuth example: python jira_oauth2_example.py")
            print("   2. Navigate to http://localhost:8000/login")
            print("   3. Authenticate with Atlassian")
            return True
        except Exception as e:
            logger.error(f"Error deleting token file: {str(e)}")
            print(f"❌ Failed to delete token: {str(e)}")
            return False
    else:
        print(f"ℹ️ No OAuth token found at {os.path.abspath(TOKEN_FILE)}")
        print("\nYou can create a new token by:")
        print("   1. Run the OAuth example: python jira_oauth2_example.py")
        print("   2. Navigate to http://localhost:8000/login")
        print("   3. Authenticate with Atlassian")
        return False


if __name__ == "__main__":
    main()
