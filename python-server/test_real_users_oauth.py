"""
OAuth Flow Test with Real Jira Users

This script guides you through testing the multi-user OAuth flow with real Jira accounts.
It will set up the server endpoints and provide instructions for authenticating with real users.

Usage:
    python test_real_users_oauth.py
"""

import logging
import os
import sys
import time
import webbrowser
from datetime import datetime
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("real_users_oauth_test.log"),
    ],
)
logger = logging.getLogger(__name__)

# Import required modules
try:
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.services.user_service import UserService
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running this from the python-server directory")
    sys.exit(1)


def setup_test_environment():
    """Setup testing environment"""
    logger.info("Setting up test environment for real user OAuth flow")

    # Check if the server is running by trying to access the health endpoint
    import requests

    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            logger.info("Server is running. Ready for OAuth testing.")
            return True
        else:
            logger.error(f"Server returned status code: {response.status_code}")
            logger.info(
                "Please start the server with: powershell -ExecutionPolicy Bypass -File .\\start_multi_user_server.ps1"
            )
            return False
    except requests.ConnectionError:
        logger.error("Cannot connect to the server at http://localhost:8000")
        logger.info(
            "Please start the server with: powershell -ExecutionPolicy Bypass -File .\\start_multi_user_server.ps1"
        )
        return False


def create_test_identifiers(count=3):
    """Create test user identifiers (not actual users)"""
    logger.info(f"Creating {count} test user identifiers")

    test_users = []
    for i in range(1, count + 1):
        identifier = f"test_user_{i}_{int(datetime.now().timestamp())}"
        test_users.append(identifier)

    return test_users


def open_oauth_flow(user_id):
    """Open OAuth flow in browser for a user ID"""
    base_url = "http://localhost:8000/api/auth/oauth/v2/login"
    full_url = f"{base_url}?user_id={quote(user_id)}"

    logger.info(f"Opening OAuth flow for user ID: {user_id}")
    logger.info(f"URL: {full_url}")

    print(f"\n{'='*80}")
    print(f"OAUTH TEST FOR USER ID: {user_id}")
    print(f"{'='*80}")
    print("1. Browser will open to start the OAuth flow")
    print("2. Log in with a different real Jira account for each test")
    print("3. Authorize the application when prompted")
    print("4. You will be redirected back to the application\n")

    input("Press Enter to open the browser...")
    webbrowser.open(full_url)

    return True


def check_token_status(user_id):
    """Check if token was successfully created for user"""
    import time

    import requests

    # Give some time for the OAuth flow to complete
    print("Waiting for OAuth flow to complete...")
    time.sleep(5)

    try:
        url = f"http://localhost:8000/api/health?user_id={quote(user_id)}"
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Failed to check token status: {response.status_code}")
            return False

        data = response.json()
        is_authenticated = data.get("authenticated", False)
        token_present = data.get("token_info", {}).get("present", False)

        if is_authenticated and token_present:
            logger.info(f"User {user_id} successfully authenticated!")
            return True
        else:
            logger.warning(
                f"User {user_id} authentication incomplete. Token present: {token_present}"
            )
            return False
    except Exception as e:
        logger.error(f"Error checking token status: {str(e)}")
        return False


def verify_jira_access(user_id):
    """Verify Jira API access for authenticated user"""
    import requests

    try:
        url = f"http://localhost:8000/api/jira/v2/projects?user_id={quote(user_id)}"
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Failed to access Jira projects: {response.status_code}")
            print(f"Error response: {response.text}")
            return False

        projects = response.json()
        project_count = len(projects)

        logger.info(
            f"Successfully retrieved {project_count} projects for user {user_id}"
        )
        print(f"\nSuccessfully retrieved {project_count} Jira projects")

        if project_count > 0:
            print("\nProject Keys:")
            for project in projects[:5]:  # Show at most 5 projects
                print(f"- {project.get('key')}: {project.get('name')}")

            if project_count > 5:
                print(f"...and {project_count - 5} more")

        return True
    except Exception as e:
        logger.error(f"Error accessing Jira API: {str(e)}")
        return False


def run_complete_test():
    """Run the complete OAuth flow test with real users"""
    # Check if server is running
    if not setup_test_environment():
        return False

    # Create test identifiers
    test_users = create_test_identifiers(3)

    # Run OAuth flow for each test user
    results = {}

    for user_id in test_users:
        print("\n\n")
        logger.info(f"Starting test for user ID: {user_id}")

        # Open OAuth flow
        open_oauth_flow(user_id)

        # Wait for user to complete OAuth flow
        input(
            "\nPress Enter when you have completed the OAuth flow (after being redirected back)..."
        )

        # Check token status
        token_success = check_token_status(user_id)

        if token_success:
            # Try to access Jira API
            api_success = verify_jira_access(user_id)
            results[user_id] = {
                "token_created": token_success,
                "api_access": api_success,
            }
        else:
            results[user_id] = {"token_created": False, "api_access": False}

    # Print summary
    print("\n\n")
    print("=" * 80)
    print("OAUTH TEST SUMMARY")
    print("=" * 80)

    all_successful = True
    for user_id, result in results.items():
        token_status = "✅ SUCCESS" if result["token_created"] else "❌ FAILED"
        api_status = "✅ SUCCESS" if result["api_access"] else "❌ FAILED"

        print(f"User ID: {user_id}")
        print(f"  Token Creation: {token_status}")
        print(f"  Jira API Access: {api_status}")
        print("")

        if not (result["token_created"] and result["api_access"]):
            all_successful = False

    if all_successful:
        print("\n✅ All tests passed successfully!")
        print("Multi-user OAuth flow is working correctly with real Jira users.")
    else:
        print("\n❌ Some tests failed. Please check the log for details.")

    return all_successful


if __name__ == "__main__":
    print("\nREAL JIRA USERS OAUTH FLOW TEST")
    print("===============================\n")
    print("This script will test the OAuth flow with real Jira user accounts.")
    print("You will need to log in with different Jira accounts for each test.")
    print("Make sure the server is running before starting the test.\n")

    start = input("Start the test? (y/n): ")
    if start.lower() == "y":
        success = run_complete_test()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("Test cancelled.")
        sys.exit(0)
