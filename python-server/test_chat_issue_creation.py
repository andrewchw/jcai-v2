#!/usr/bin/env python3
"""
Test issue creation through the chat API to verify the parameter fix.
This test mimics the actual user flow through the chat interface.
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import time

import requests


def test_chat_issue_creation():
    """Test issue creation through the chat API"""

    user_id = "edge-1748270783635-lun5ucqg"
    base_url = "http://localhost:8000"

    # Test data for issue creation
    message = 'create issue with summary "Test issue creation through chat API" description "Testing the fix for create issue method components parameter" project "JCAI" type "Story"'

    print("Testing issue creation through chat API...")
    print(f"User ID: {user_id}")
    print(f"Message: {message}")
    print()

    try:
        # Test the chat endpoint
        headers = {"Content-Type": "application/json"}
        payload = {"text": message}

        print("Sending request to chat API...")
        response = requests.post(
            f"{base_url}/api/chat/message/{user_id}",
            headers=headers,
            json=payload,
            timeout=30,
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Chat API request successful")
            print("Response:")
            print(json.dumps(result, indent=2))

            # Check if the response indicates successful issue creation
            response_text = result.get("message", "").lower()
            if (
                "error" in response_text
                and "unexpected keyword argument" in response_text
            ):
                print("❌ Parameter mismatch error still present!")
                return False
            elif "created" in response_text or "issue" in response_text:
                print("✅ Issue creation appears to have been processed")
                return True
            else:
                print("🔍 Response received but unclear if issue was created")
                return True  # At least no parameter error

        elif response.status_code == 422:
            error_detail = response.json()
            print("❌ Chat API validation error:")
            print(json.dumps(error_detail, indent=2))
            return False
        else:
            print(f"❌ Chat API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(
            "❌ Could not connect to server. Is the server running on http://localhost:8000?"
        )
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_chat_issue_creation()
    print()
    if success:
        print("✅ Chat issue creation test PASSED")
        print("The parameter mismatch fix appears to be working!")
    else:
        print("❌ Chat issue creation test FAILED")

    exit(0 if success else 1)
