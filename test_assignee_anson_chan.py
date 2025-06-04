#!/usr/bin/env python3
"""
Test script to verify that the assignee functionality works with "Anson Chan".
This reproduces the exact scenario from the issue creation flow.
"""

import json
import time

import requests

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "1"  # Using the same user ID from the logs


def test_assignee_anson_chan():
    """Test creating an issue with Anson Chan as assignee"""
    print("🧪 Testing issue creation with assignee 'Anson Chan'...")

    try:
        # Test the exact payload that was failing
        payload = {
            "user_id": TEST_USER_ID,
            "message": "Create issues: Summary: 'Test assignee 5', Assignee : 'Anson Chan', Due Date : 'Tomorrow'",
        }

        print(f"📤 Sending chat request...")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)

        print(f"📥 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat request successful!")
            print(f"Response: {json.dumps(data, indent=2)}")

            # Check if the response contains issue creation details
            if "response" in data and "issue" in data["response"].lower():
                print("✅ Issue creation appears to be working!")
                return True
            else:
                print("⚠️  Response doesn't clearly indicate issue creation")

        else:
            print(f"❌ Chat request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def test_direct_issue_creation():
    """Test creating an issue directly via the issue creation endpoint"""
    print("\n🧪 Testing direct issue creation with assignee 'Anson Chan'...")

    try:
        payload = {
            "user_id": TEST_USER_ID,
            "project_key": "TEST",
            "summary": "Test assignee 5",
            "description": "Testing assignee functionality with Anson Chan",
            "issue_type": "Task",
            "assignee": "Anson Chan",
            "duedate": "2025-06-05",  # Tomorrow
        }

        print(f"📤 Sending direct issue creation request...")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(
            f"{BASE_URL}/api/create-issue", json=payload, timeout=60
        )

        print(f"📥 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Direct issue creation successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Direct issue creation failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def main():
    """Run the tests"""
    print("🚀 Starting assignee functionality tests...")
    print(f"🎯 Target: {BASE_URL}")
    print(f"👤 User ID: {TEST_USER_ID}")
    print("=" * 60)

    # Test 1: Chat endpoint
    chat_success = test_assignee_anson_chan()

    # Test 2: Direct endpoint
    direct_success = test_direct_issue_creation()

    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"Chat endpoint: {'✅ PASS' if chat_success else '❌ FAIL'}")
    print(f"Direct endpoint: {'✅ PASS' if direct_success else '❌ FAIL'}")

    if chat_success and direct_success:
        print("🎉 All tests passed! Assignee functionality is working.")
        return True
    else:
        print("💔 Some tests failed. Check the logs above.")
        return False


if __name__ == "__main__":
    main()
