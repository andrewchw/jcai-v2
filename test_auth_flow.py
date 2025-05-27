#!/usr/bin/env python3
"""
Test the complete authentication flow from extension to server.
This script simulates what happens when a user authenticates.
"""

import json
import time
import uuid

import requests

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER_ID = f"test-{int(time.time())}-{str(uuid.uuid4())[:8]}"


def test_authentication_flow():
    """Test the complete authentication flow and measure performance."""
    print(f"Testing authentication flow for user: {TEST_USER_ID}")

    # Step 1: Check unauthenticated chat endpoint
    print("\n1. Testing unauthenticated chat request...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/message/{TEST_USER_ID}",
            json={"message": "Hello, can you help me?"},
            headers={"Content-Type": "application/json"},
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")

    # Step 2: Test token status for non-existent user
    print("\n2. Testing token status for unauthenticated user...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/oauth/v2/token/status",
            params={"user_id": TEST_USER_ID},
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")

    # Step 3: Test health endpoint
    print("\n3. Testing server health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")

    # Step 4: Test multiple parallel token checks (simulating extension behavior)
    print("\n4. Testing parallel authentication calls performance...")
    start_time = time.time()

    def check_token_status():
        try:
            response = requests.get(
                f"{API_BASE_URL}/auth/oauth/v2/token/status",
                params={"user_id": TEST_USER_ID},
                timeout=5,
            )
            return response.status_code, response.elapsed.total_seconds()
        except Exception as e:
            return None, str(e)

    def fetch_user_info():
        try:
            # This would be the user info endpoint if implemented
            # For now, simulate with health check
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            return response.status_code, response.elapsed.total_seconds()
        except Exception as e:
            return None, str(e)

    # Sequential calls (current behavior)
    print("   Sequential calls:")
    seq_start = time.time()
    token_result = check_token_status()
    user_result = fetch_user_info()
    seq_time = time.time() - seq_start
    print(f"     Token check: {token_result[0]} ({token_result[1]:.3f}s)")
    print(f"     User info: {user_result[0]} ({user_result[1]:.3f}s)")
    print(f"     Total sequential time: {seq_time:.3f}s")

    # Parallel calls (optimized behavior)
    print("   Parallel calls:")
    par_start = time.time()
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as executor:
        token_future = executor.submit(check_token_status)
        user_future = executor.submit(fetch_user_info)

        token_result_par = token_future.result()
        user_result_par = user_future.result()
    par_time = time.time() - par_start
    print(f"     Token check: {token_result_par[0]} ({token_result_par[1]:.3f}s)")
    print(f"     User info: {user_result_par[0]} ({user_result_par[1]:.3f}s)")
    print(f"     Total parallel time: {par_time:.3f}s")
    print(
        f"     Performance improvement: {((seq_time - par_time) / seq_time * 100):.1f}%"
    )


def test_chat_pagination():
    """Test the chat system with pagination commands."""
    print(f"\n5. Testing chat pagination commands...")

    test_messages = [
        "show me my jira issues",
        "show more issues",
        "tell me about project management",
        "show more",
        "what are my recent tasks?",
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n   Message {i}: '{message}'")
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat/message/{TEST_USER_ID}",
                json={"message": message},
                headers={"Content-Type": "application/json"},
            )
            print(f"     Status: {response.status_code}")
            result = response.json()
            print(f"     Response: {result.get('response', 'No response')[:100]}...")
            if "conversation_context" in result:
                print(f"     Context preserved: Yes")
            else:
                print(f"     Context preserved: No")
        except Exception as e:
            print(f"     Error: {e}")

        # Small delay between messages
        time.sleep(0.5)


if __name__ == "__main__":
    print("JIRA Extension Authentication Flow Test")
    print("=" * 50)

    test_authentication_flow()
    test_chat_pagination()

    print("\n" + "=" * 50)
    print("Test completed!")
