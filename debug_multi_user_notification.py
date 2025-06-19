#!/usr/bin/env python3
"""
Debug script to test multi-user Jira service authentication
"""
import requests
import json
import sys
import os

# Add the python-server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-server'))

from app.core.database import get_db
from app.services.multi_user_jira_service import MultiUserJiraService
import sqlite3

def test_multi_user_auth():
    """Test multi-user Jira service authentication"""
    try:
        # Create a database session
        db = next(get_db())

        # Initialize multi-user service
        print("Initializing multi-user Jira service...")
        multi_jira_service = MultiUserJiraService(db)

        # Get the service for our test user
        user_id = "edge-1749460706591-hh3bdgu8"
        print(f"Getting Jira service for user {user_id}...")
        jira_service = multi_jira_service.get_jira_service(user_id)

        if not jira_service:
            print(f"ERROR: Could not get Jira service for user {user_id}")
            return

        print(f"Jira service created successfully")

        # Check if OAuth token is available
        if hasattr(jira_service, '_oauth2_token') and jira_service._oauth2_token:
            print(f"OAuth token available: {bool(jira_service._oauth2_token.get('access_token'))}")
            # Don't print the actual token for security
        else:
            print("ERROR: No OAuth token available")
            return

        # Check cloud ID
        if hasattr(jira_service, '_cached_cloud_id'):
            print(f"Cached cloud ID: {jira_service._cached_cloud_id}")

        # Try to get cloud ID
        cloud_id = jira_service._get_cloud_id()
        print(f"Retrieved cloud ID: {cloud_id}")

        # Test basic user info
        try:
            user_info = jira_service.myself()
            print(f"User info: {user_info.get('displayName', 'Unknown')} ({user_info.get('accountId', 'No ID')})")
        except Exception as e:
            print(f"ERROR getting user info: {str(e)}")
            return

        # Test issue retrieval
        try:
            issue_key = 'JCAI-124'
            issue_data = jira_service.get_issue(issue_key)
            if issue_data:
                print(f"Issue data: {issue_data.get('key', 'No key')} - {issue_data.get('fields', {}).get('summary', 'No summary')}")
            else:
                print(f"ERROR: Could not get issue {issue_key}")
                return
        except Exception as e:
            print(f"ERROR getting issue: {str(e)}")
            return            # Now test the notification API directly
            if cloud_id and jira_service._oauth2_token and "access_token" in jira_service._oauth2_token:
                # Try different notification payload formats
                notification_payloads = [
                    {
                        "subject": f"Test Notification for {issue_key}",
                        "textBody": "This is a test notification from the JCAI system.",
                        "htmlBody": "<p>This is a test notification from the JCAI system.</p>",
                        "to": {
                            "users": [
                                {
                                    "accountId": user_info.get('accountId')
                                }
                            ]
                        }
                    },
                    {
                        "subject": f"Test Notification for {issue_key}",
                        "textBody": "This is a test notification from the JCAI system.",
                        "htmlBody": "<p>This is a test notification from the JCAI system.</p>",
                        "to": {
                            "users": [user_info.get('accountId')]
                        }
                    },
                    {
                        "subject": f"Test Notification for {issue_key}",
                        "textBody": "This is a test notification from the JCAI system.",
                        "htmlBody": "<p>This is a test notification from the JCAI system.</p>",
                        "to": {
                            "assignee": True
                        }
                    }
                ]

                for i, notification_payload in enumerate(notification_payloads):
                    print(f"\nTesting notification format {i+1}...")
                    print(f"Payload: {json.dumps(notification_payload, indent=2)}")

                    url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}/notify"
                    headers = {
                        "Authorization": f"Bearer {jira_service._oauth2_token['access_token']}",
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }

                    response = requests.post(url, headers=headers, json=notification_payload)
                    print(f"Response status: {response.status_code}")
                    print(f"Response text: {response.text}")

                    if response.status_code in [200, 204]:
                        print(f"SUCCESS: Notification format {i+1} worked!")
                        break
                    else:
                        print(f"FAILED: Notification format {i+1} failed")
            else:
                print("ERROR: Missing cloud ID or OAuth token")

        db.close()

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multi_user_auth()
