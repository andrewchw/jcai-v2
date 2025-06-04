#!/usr/bin/env python3
"""
Test script to verify Jira issue creation with assignee and due date
"""
import json
from datetime import datetime, timedelta

import requests


def test_issue_creation():
    """Test creating a Jira issue with assignee and due date"""

    # Test data
    test_message = 'Create issues: Summary : "Task Title Test", Assignee : "Anson Chan", Due Date : "Friday"'
    # API endpoint - correct endpoint path and payload format
    user_id = "test@example.com"
    url = f"http://localhost:8000/api/chat/message/{user_id}"

    # Headers
    headers = {"Content-Type": "application/json"}

    # Payload - correct format for ChatMessage
    payload = {"text": test_message}
    print(f"Testing issue creation...")
    print(f"User ID: {user_id}")
    print(f"Message: {test_message}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        # Make the request
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")

            # Check if issue was created successfully
            if "message" in response_data:
                message = response_data["message"]
                if "created successfully" in message.lower():
                    print("\n✅ Issue creation appears successful")

                    # Look for issue key in response
                    if "key" in message or any(
                        word.startswith(("TEST-", "PROJ-", "JIRA-"))
                        for word in message.split()
                    ):
                        print("✅ Issue key found in response")
                    else:
                        print("⚠️  No issue key found in response")
                else:
                    print(f"⚠️  Unexpected response message: {message}")
            else:
                print("⚠️  No message in response")

        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response text: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    test_issue_creation()
