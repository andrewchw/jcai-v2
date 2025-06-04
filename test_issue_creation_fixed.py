#!/usr/bin/env python3
"""
Test script to verify Jira issue creation with assignee and due date
"""
import json
from datetime import datetime, timedelta

import requests


def test_issue_creation():
    """Test creating a Jira issue with assignee and due date"""

    # Test data with authenticated user
    test_message = 'Create issues: Summary : "Task Title Test", Assignee : "Anson Chan", Due Date : "Friday"'
    user_id = "edge-1748270783635-lun5ucqg"  # Authenticated user

    # API endpoint - corrected to match actual route
    url = f"http://localhost:8000/api/chat/message/{user_id}"

    # Headers
    headers = {"Content-Type": "application/json"}

    # Payload - using "text" field as per ChatMessage model
    payload = {"text": test_message}

    print(f"Testing issue creation...")
    print(f"User ID: {user_id}")
    print(f"Message: {test_message}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        # Make the request
        response = requests.post(url, headers=headers, json=payload, timeout=60)

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
                    if "JCAI-" in message:
                        print("✅ Issue key found in response")
                        # Extract issue key
                        import re

                        issue_key_match = re.search(r"JCAI-\d+", message)
                        if issue_key_match:
                            issue_key = issue_key_match.group()
                            print(f"✅ Created issue: {issue_key}")
                    else:
                        print("⚠️  No issue key found in response")

                    # Check if assignee and due date were mentioned
                    if "assignee" in message.lower() or "anson" in message.lower():
                        print("✅ Assignee mentioned in response")
                    else:
                        print("⚠️  Assignee not mentioned in response")

                    if "due date" in message.lower() or "friday" in message.lower():
                        print("✅ Due date mentioned in response")
                    else:
                        print("⚠️  Due date not mentioned in response")

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
