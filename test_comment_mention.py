#!/usr/bin/env python3
"""
Test adding a comment with user mention as alternative to notifications
"""
import requests
import json

def test_comment_with_mention():
    """Test adding a comment with user mention"""

    # From the previous successful test
    cloud_id = "5005c0b6-0e2a-4cbc-9a81-5cb043c0140b"
    issue_key = "JCAI-124"
    account_id = "5eafc56196bbcb0b8565b9ee"

    # Get the access token
    with open("oauth_token.json", "r") as f:
        token_data = json.load(f)

    access_token = token_data.get("access_token")
    if not access_token:
        print("ERROR: No access token found")
        return

    # Test adding a comment with user mention
    comment_payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a test notification from the JCAI system. "
                        },
                        {
                            "type": "mention",
                            "attrs": {
                                "id": account_id,
                                "text": "@Andrew Chan"
                            }
                        },
                        {
                            "type": "text",
                            "text": ", please review this issue."
                        }
                    ]
                }
            ]
        }
    }

    url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}/comment"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    print(f"Testing comment with mention for {issue_key}...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(comment_payload, indent=2)}")

    response = requests.post(url, headers=headers, json=comment_payload)
    print(f"Response status: {response.status_code}")
    print(f"Response text: {response.text}")

    if response.status_code in [200, 201]:
        print("SUCCESS: Comment with mention added!")
        return True
    else:
        print("FAILED: Comment with mention failed")
        return False

if __name__ == "__main__":
    test_comment_with_mention()
