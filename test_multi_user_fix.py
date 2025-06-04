#!/usr/bin/env python3
"""
Test script to verify the UserService initialization fix in multi-user functionality.
This tests the issue creation flow that was previously failing with UserService.__init__() error.
"""

import json
import time

import requests

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"


def test_server_health():
    """Test if the server is running and healthy."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✓ Server health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Server health check failed: {e}")
        return False


def test_chat_endpoint():
    """Test the chat endpoint that uses multi-user functionality."""
    try:
        payload = {
            "message": "Create a test issue for testing multi-user functionality",
            "user_id": TEST_USER_ID,
        }

        print(f"Sending chat request with payload: {json.dumps(payload, indent=2)}")

        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)

        print(f"Chat response status: {response.status_code}")
        print(f"Chat response headers: {dict(response.headers)}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"✓ Chat endpoint successful")
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print(f"✗ Chat endpoint failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Chat endpoint test failed: {e}")
        return False


def test_multi_user_jira_service():
    """Test the multi-user Jira service initialization directly."""
    try:
        # Test endpoint that uses multi-user service
        payload = {
            "user_id": TEST_USER_ID,
            "project_key": "TEST",
            "summary": "Test issue for multi-user functionality",
            "description": "Testing UserService initialization fix",
            "issue_type": "Task",
        }

        print(
            f"Testing multi-user issue creation with payload: {json.dumps(payload, indent=2)}"
        )

        response = requests.post(
            f"{BASE_URL}/api/create-issue", json=payload, timeout=30
        )

        print(f"Create issue response status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"✓ Multi-user issue creation successful")
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print(f"✗ Multi-user issue creation failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Multi-user issue creation test failed: {e}")
        return False


def main():
    """Run all tests to verify the fix."""
    print("=" * 60)
    print("Testing Multi-User Functionality Fix")
    print("=" * 60)

    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(3)

    tests_passed = 0
    total_tests = 3

    # Test 1: Server health
    print("\n1. Testing server health...")
    if test_server_health():
        tests_passed += 1

    # Test 2: Chat endpoint (uses multi-user functionality)
    print("\n2. Testing chat endpoint...")
    if test_chat_endpoint():
        tests_passed += 1

    # Test 3: Direct multi-user service test
    print("\n3. Testing multi-user issue creation...")
    if test_multi_user_jira_service():
        tests_passed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"Tests completed: {tests_passed}/{total_tests} passed")

    if tests_passed == total_tests:
        print("✓ All tests passed! Multi-user functionality is working correctly.")
    else:
        print("✗ Some tests failed. Check the logs above for details.")

    print("=" * 60)


if __name__ == "__main__":
    main()
