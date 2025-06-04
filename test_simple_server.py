#!/usr/bin/env python3
"""
Simple test to check if server is responding
"""
import json

import requests


def test_server_health():
    """Test if the server is running and responding"""

    try:
        # Test health endpoint first
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"Health check status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not running")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_simple_chat():
    """Test a simple chat message"""

    if not test_server_health():
        return

    url = "http://localhost:8000/chat"
    headers = {"Content-Type": "application/json"}
    payload = {"message": "Hello", "user_email": "test@example.com"}

    print(f"\nTesting simple chat...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Chat response status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        else:
            print(f"Error: {response.text}")

    except requests.exceptions.Timeout:
        print("❌ Chat request timeout")
    except Exception as e:
        print(f"❌ Chat error: {e}")


if __name__ == "__main__":
    test_simple_chat()
