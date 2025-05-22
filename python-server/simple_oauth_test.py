"""
Simple OAuth Test Script

This script provides a simple way to test the OAuth flow with a real Jira account.
It will open the OAuth login URL in a browser and then check if the token was created.
"""

import webbrowser
import time
import requests
import json
from urllib.parse import quote

def main():
    print("\n============================================")
    print("SIMPLE OAUTH TEST FOR JIRA CHATBOT API")
    print("============================================\n")
    
    # Create a unique test user ID
    import time
    user_id = f"test_user_{int(time.time())}"
    
    print(f"Using test user ID: {user_id}")
    print("This ID will be used to track the OAuth token\n")
    
    # Check server status
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code != 200:
            print(f"ERROR: Server returned status code {response.status_code}")
            print("Make sure the server is running.")
            return
    except Exception as e:        
        print(f"ERROR: Could not connect to server: {str(e)}")
        print("Make sure the server is running.")
        return
    
    print("Server is running and healthy.\n")
    
    # Generate the URL for the OAuth login - using the updated route
    base_url = "http://localhost:8000/api/auth/oauth/v2/login"
    full_url = f"{base_url}?user_id={quote(user_id)}"
    
    # Also create a direct URL to test the root-level callback
    direct_url = f"http://localhost:8000/callback?user_id={quote(user_id)}&success=true"
    
    print("INSTRUCTIONS:")
    print("1. The OAuth login page will open in your browser")
    print("2. Log in with your Jira account credentials")
    print("3. Authorize the application when prompted")
    print("4. You will be redirected back to the application")
    print("5. This script will check if the token was created successfully\n")
    
    print("TESTING OPTIONS:")
    print("1. Press Enter to open the normal OAuth flow")
    print("2. Press 'D' then Enter to directly test the callback URL\n")
    choice = input("Enter your choice (Enter or D): ").strip().upper()
    
    if choice == 'D':
        print("Testing direct callback URL...")
        webbrowser.open(direct_url)
    else:
        print("Opening normal OAuth flow...")
        webbrowser.open(full_url)
    
    print("\nBrowser opened. Please complete the OAuth flow...")
    
    # Check token status after a delay
    print("Waiting for OAuth flow to complete...")
    time.sleep(10)  # Give the user some time to complete the OAuth flow
    
    # Check token status
    try:
        url = f"http://localhost:8000/api/health?user_id={quote(user_id)}"
        print(f"Checking token status at: {url}")
        
        response = requests.get(url)
        if response.status_code != 200:
            print(f"ERROR: Server returned status code {response.status_code}")
            return
        
        data = response.json()
        is_authenticated = data.get("authenticated", False)
        token_info = data.get("token_info", {})
        token_present = token_info.get("present", False)
        
        print("\n============================================")
        print("AUTHENTICATION RESULT")
        print("============================================")
        print(f"Authenticated: {is_authenticated}")
        print(f"Token present: {token_present}")
        
        if "expires_in" in token_info:
            print(f"Token expires in: {token_info['expires_in']} seconds")
        if is_authenticated and token_present:
            print("\nSUCCESS: OAuth authentication completed successfully!")
            
            # Check debug info first
            print("\n============================================")
            print("CHECKING DEBUG INFORMATION")
            print("============================================")
            try:
                debug_url = f"http://localhost:8000/api/debug/user-token-info?user_id={quote(user_id)}"
                debug_response = requests.get(debug_url)
                
                if debug_response.status_code != 200:
                    print(f"ERROR: Could not access debug API. Status code: {debug_response.status_code}")
                    print(f"Response: {debug_response.text}")
                else:
                    debug_info = debug_response.json()
                    print(f"\nToken Information for user {user_id}:")
                    print(f"Token present: {debug_info.get('token', {}) != {}}")
                    print(f"Cloud ID: {debug_info.get('cloud_id', 'Not available')}")
                    print(f"Is connected: {debug_info.get('is_connected', False)}")
                    
                    # Check OAuth config
                    config_url = "http://localhost:8000/api/debug/oauth-config"
                    config_response = requests.get(config_url)
                    
                    if config_response.status_code == 200:
                        config = config_response.json()
                        print("\nOAuth Configuration:")                        
                        print(f"Client ID: {config.get('client_id', 'Not available')}")
                        print(f"Callback URL: {config.get('callback_url', 'Not available')}")
                        print(f"Cloud ID from env: {config.get('cloud_id', 'Not available')}")
                    else:
                        print(f"ERROR: Could not access OAuth config. Status code: {config_response.status_code}")
            except Exception as e:
                print(f"Error checking debug information: {str(e)}")
              
            # Test Jira API access
            print("\n============================================")
            print("TESTING JIRA API ACCESS")
            print("============================================")
            # First, retrieve user information
            print("Attempting to retrieve your Jira user information...")
            try:
                user_url = f"http://localhost:8000/api/jira/v2/user?user_id={quote(user_id)}"
                user_response = requests.get(user_url)
                
                if user_response.status_code != 200:
                    print(f"ERROR: Could not retrieve user information. Status code: {user_response.status_code}")
                    print(f"Response: {user_response.text}")
                    print(f"URL attempted: {user_url}")
                else:
                    user_info = user_response.json()
                    print("\nSUCCESS: Retrieved Jira user information:")
                    print(f"Display Name: {user_info.get('displayName', 'N/A')}")
                    print(f"Email: {user_info.get('emailAddress', 'N/A')}")
                    print(f"Account ID: {user_info.get('accountId', 'N/A')}")
                    print(f"Active: {user_info.get('active', 'N/A')}")
                    print(f"Time Zone: {user_info.get('timeZone', 'N/A')}")
            except Exception as e:
                print(f"Error retrieving user information: {str(e)}")
                
            # Then try to retrieve projects
            print("\nAttempting to retrieve your Jira projects...")
            try:
                url = f"http://localhost:8000/api/jira/v2/projects?user_id={quote(user_id)}"
                response = requests.get(url)
                
                if response.status_code != 200:
                    print(f"ERROR: Could not access Jira projects API. Status code: {response.status_code}")
                    print(f"Response: {response.text}")
                    print(f"URL attempted: {url}")
                    print("\nNOTE: If you're seeing a 404 error, the server may need to be restarted to apply recent changes.")
                    print("Please restart the server and try again.")
                else:
                    projects = response.json()
                    print(f"\nSuccessfully retrieved {len(projects)} projects!")
                    
                    if len(projects) > 0:
                        print("\nYour Jira Projects:")
                        for idx, project in enumerate(projects[:5]):  # Show at most 5 projects
                            print(f"{idx+1}. {project.get('key')}: {project.get('name')}")
            except Exception as e:
                print(f"Error testing Jira projects API access: {str(e)}")
        else:
            print("\nFAILURE: OAuth authentication did not complete successfully.")
            print("Please check the server logs for more details.")
    except Exception as e:
        print(f"Error checking token status: {str(e)}")

if __name__ == "__main__":
    main()
