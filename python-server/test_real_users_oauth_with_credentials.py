"""
OAuth Flow Test with Real Jira Users

This script guides you through testing the multi-user OAuth flow with real Jira accounts.
It will set up the server endpoints and provide instructions for authenticating with real users.

Usage:
    python test_real_users_oauth_with_credentials.py
"""

import os
import sys
import logging
import webbrowser
from datetime import datetime
from urllib.parse import quote
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('real_users_oauth_test.log')
    ]
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
            logger.info("Please start the server with: powershell -ExecutionPolicy Bypass -File .\\start_multi_user_server.ps1")
            return False
    except requests.ConnectionError:
        logger.error("Cannot connect to the server at http://localhost:8000")
        logger.info("Please start the server with: powershell -ExecutionPolicy Bypass -File .\\start_multi_user_server.ps1")
        return False

def get_test_users_info():
    """Get information about the test users from user input"""
    print("\nEnter details for the test users you've created in Jira.")
    print("This information is only for your reference during testing.\n")
    
    test_users = []
    user_count = int(input("How many Jira test users do you want to test with? (1-3): "))
    
    if not 1 <= user_count <= 3:
        print("Please choose between 1 and 3 test users.")
        return get_test_users_info()
    
    for i in range(1, user_count+1):
        print(f"\nTest User {i}:")
        email = input(f"  Email address for User {i}: ")
        username = input(f"  Username (if different from email): ")
        description = input(f"  Brief description (e.g., 'Admin User', 'Regular User'): ")
        
        # Generate a unique ID for this test user
        user_id = f"test_user_{i}_{int(datetime.now().timestamp())}"
        
        test_users.append({
            "id": user_id,
            "email": email,
            "username": username or email,
            "description": description,
        })
        
    # Save the test user information to a file for reference
    with open("test_users_reference.json", "w") as f:
        json.dump(test_users, f, indent=2)
    
    print("\nTest user information saved to test_users_reference.json for your reference.")
    
    return test_users

def open_oauth_flow(user):
    """Open OAuth flow in browser for a test user"""
    base_url = "http://localhost:8000/api/auth/oauth/v2/login"
    user_id = user["id"]
    full_url = f"{base_url}?user_id={quote(user_id)}"
    
    logger.info(f"Opening OAuth flow for user ID: {user_id}")
    logger.info(f"URL: {full_url}")
    
    print(f"\n{'='*80}")
    print(f"OAUTH TEST FOR USER: {user['description']}")
    print(f"ID: {user_id}")
    print(f"{'='*80}")
    print(f"Email to use: {user['email']}")
    print(f"Username: {user['username']}")
    print(f"{'='*80}")
    print("1. Browser will open to start the OAuth flow")
    print("2. Log in with the Jira account details shown above")
    print("3. Authorize the application when prompted")
    print("4. You will be redirected back to the application\n")
    
    input("Press Enter to open the browser...")
    webbrowser.open(full_url)
    
    return True

def check_token_status(user):
    """Check if token was successfully created for user"""
    import requests
    import time
    
    user_id = user["id"]
    
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
            logger.info(f"User {user_id} ({user['email']}) successfully authenticated!")
            return True
        else:
            logger.warning(f"User {user_id} ({user['email']}) authentication incomplete. Token present: {token_present}")
            return False
    except Exception as e:
        logger.error(f"Error checking token status: {str(e)}")
        return False

def verify_jira_access(user):
    """Verify Jira API access for authenticated user"""
    import requests
    
    user_id = user["id"]
    
    try:
        url = f"http://localhost:8000/api/jira/v2/projects?user_id={quote(user_id)}"
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"Failed to access Jira projects: {response.status_code}")
            print(f"Error response: {response.text}")
            return False
        
        projects = response.json()
        project_count = len(projects)
        
        logger.info(f"Successfully retrieved {project_count} projects for user {user_id} ({user['email']})")
        print(f"\nSuccessfully retrieved {project_count} Jira projects for {user['email']}")
        
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
    
    # Get test user information
    test_users = get_test_users_info()
    
    # Run OAuth flow for each test user
    results = {}
    
    for user in test_users:
        print("\n\n")
        logger.info(f"Starting test for user: {user['email']} (ID: {user['id']})")
        
        # Open OAuth flow
        open_oauth_flow(user)
        
        # Wait for user to complete OAuth flow
        input("\nPress Enter when you have completed the OAuth flow (after being redirected back)...")
        
        # Check token status
        token_success = check_token_status(user)
        
        if token_success:
            # Try to access Jira API
            api_success = verify_jira_access(user)
            results[user["id"]] = {
                "email": user["email"],
                "token_created": token_success,
                "api_access": api_success
            }
        else:
            results[user["id"]] = {
                "email": user["email"],
                "token_created": False,
                "api_access": False
            }
    
    # Print summary
    print("\n\n")
    print(f"{'='*80}")
    print(f"OAUTH TEST SUMMARY")
    print(f"{'='*80}")
    
    all_successful = True
    for user_id, result in results.items():
        token_status = "✅ SUCCESS" if result["token_created"] else "❌ FAILED"
        api_status = "✅ SUCCESS" if result["api_access"] else "❌ FAILED"
        
        print(f"User: {result['email']}")
        print(f"  ID: {user_id}")
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
    print("This script will test the OAuth flow with your real Jira user accounts.")
    print("You'll need to provide information about the Jira accounts you've created.")
    print("Make sure the server is running before starting the test.\n")
    
    start = input("Start the test? (y/n): ")
    if start.lower() == 'y':
        success = run_complete_test()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("Test cancelled.")
        sys.exit(0)
