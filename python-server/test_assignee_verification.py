#!/usr/bin/env python3
"""
Test script to verify that assignee lookup is working correctly
by checking the created Jira issue details.
"""

import json

import requests


def test_assignee_verification():
    """Test that the assignee was properly set in the created issue"""

    # API Configuration
    api_base = "http://localhost:8000"
    user_id = "edge-1748270783635-lun5ucqg"  # Authenticated user
    issue_key = "JCAI-74"  # The issue we just created

    print("Testing assignee verification...")
    print(f"Checking issue: {issue_key}")
    print()

    # Get issue details to verify assignee was set correctly
    url = f"{api_base}/api/chat/message/{user_id}"
    payload = {"text": f"show me details for {issue_key}"}

    print("Request:")
    print(json.dumps(payload, indent=2))
    print()

    try:
        response = requests.post(url, json=payload, timeout=30)

        print(f"Status Code: {response.status_code}")
        print("Response:")
        response_data = response.json()
        print(json.dumps(response_data, indent=2))

        # Check if the response mentions the assignee
        if response.status_code == 200:
            text = response_data.get("text", "")

            if "Anson Chan" in text:
                print("\n✅ SUCCESS: Assignee 'Anson Chan' found in issue details!")
            elif "assignee" in text.lower() or "assigned" in text.lower():
                print(
                    "\n⚠️  PARTIAL: Issue has assignee info but may not be 'Anson Chan'"
                )
                print(f"Response text: {text}")
            else:
                print("\n❌ ISSUE: No assignee information found in response")
                print(f"Response text: {text}")
        else:
            print(f"\n❌ ERROR: Request failed with status {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed - {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    test_assignee_verification()
