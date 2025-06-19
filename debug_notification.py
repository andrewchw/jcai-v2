#!/usr/bin/env python3
"""
Debug script to test Jira notification API directly
"""
import requests
import json
import sys
import os

# Add the python-server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-server'))

from app.services.jira_service import jira_service

def test_notification_direct():
    """Test Jira notification API directly"""
    try:
        # Initialize the service
        print("Initializing Jira service...")

        # Get user info
        user_info = jira_service.myself()
        if not user_info:
            print("ERROR: Could not get user info")
            return

        print(f"User info: {user_info.get('displayName', 'Unknown')} ({user_info.get('accountId', 'No ID')})")

        # Get the issue
        issue_key = 'JCAI-124'
        print(f"Getting issue {issue_key}...")
        issue_data = jira_service.get_issue(issue_key)

        if not issue_data:
            print(f"ERROR: Could not get issue {issue_key}")
            return

        print(f"Issue data: {issue_data.get('key', 'No key')} - {issue_data.get('fields', {}).get('summary', 'No summary')}")

        # Create notification payload
        notification_payload = {
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
        }

        print(f"Notification payload: {json.dumps(notification_payload, indent=2)}")

        # Test the notification
        print(f"Sending notification for {issue_key}...")
        success = jira_service.send_issue_notification(issue_key, notification_payload)

        print(f"Notification result: {'SUCCESS' if success else 'FAILED'}")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_notification_direct()
