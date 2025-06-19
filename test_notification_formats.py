#!/usr/bin/env python3
"""
Simple test for Jira notification API formats
"""
import requests
import json

def test_notification_formats():
    """Test different notification payload formats"""

    # From the previous successful test
    cloud_id = "5005c0b6-0e2a-4cbc-9a81-5cb043c0140b"
    issue_key = "JCAI-124"
    account_id = "5eafc56196bbcb0b8565b9ee"

    # You'll need to manually get the access token from oauth_token.json
    with open("oauth_token.json", "r") as f:
        token_data = json.load(f)

    access_token = token_data.get("access_token")
    if not access_token:
        print("ERROR: No access token found")
        return

    # Test different notification payload formats
    notification_payloads = [
        {
            "subject": f"Test Notification for {issue_key}",
            "textBody": "This is a test notification from the JCAI system.",
            "htmlBody": "<p>This is a test notification from the JCAI system.</p>",
            "to": {
                "users": [account_id]  # Simple string format
            }
        },
        {
            "subject": f"Test Notification for {issue_key}",
            "textBody": "This is a test notification from the JCAI system.",
            "htmlBody": "<p>This is a test notification from the JCAI system.</p>",
            "to": {
                "assignee": True  # Send to assignee
            }
        },
        {
            "subject": f"Test Notification for {issue_key}",
            "textBody": "This is a test notification from the JCAI system.",
            "htmlBody": "<p>This is a test notification from the JCAI system.</p>",
            "to": {
                "reporter": True  # Send to reporter
            }
        },
        {
            "subject": f"Test Notification for {issue_key}",
            "textBody": "This is a test notification from the JCAI system.",
            "htmlBody": "<p>This is a test notification from the JCAI system.</p>",
            "to": {
                "watchers": True  # Send to watchers
            }
        }
    ]

    url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}/notify"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    for i, notification_payload in enumerate(notification_payloads):
        print(f"\nTesting notification format {i+1}...")
        print(f"Payload: {json.dumps(notification_payload, indent=2)}")

        response = requests.post(url, headers=headers, json=notification_payload)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")

        if response.status_code in [200, 204]:
            print(f"SUCCESS: Notification format {i+1} worked!")
        else:
            print(f"FAILED: Notification format {i+1} failed")

if __name__ == "__main__":
    test_notification_formats()
