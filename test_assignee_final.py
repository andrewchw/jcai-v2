"""
Test script for assignee functionality with user sync.

This script tests:
1. Creating an issue with an assignee
2. Verifying the user lookup and sync functionality
3. Ensuring the assignee field is properly set in Jira
"""

import json
import time

import requests

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = "edge-1748270783635-lun5ucqg"  # Authenticated user ID


def test_user_sync_and_assignee():
    """Test user synchronization and assignee assignment"""
    print("=" * 60)
    print("TESTING USER SYNC AND ASSIGNEE FUNCTIONALITY")
    print("=" * 60)

    # Test 1: Create issue with assignee
    print("\n1. Testing issue creation with assignee...")

    test_message = 'Create issues: Summary : "Test Assignee Sync", Assignee : "Anson Chan", Due Date : "Monday"'

    payload = {"text": test_message}

    try:
        print(f"Sending request to: {BASE_URL}/api/chat/message/{USER_ID}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(
            f"{BASE_URL}/api/chat/message/{USER_ID}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60,
        )

        print(f"\nResponse Status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")

            # Check if issue was created
            if "Successfully created issue" in response_data.get("message", ""):
                print("✓ Issue creation successful!")

                # Extract issue key from response
                message = response_data.get("message", "")
                if "JCAI-" in message:
                    issue_key = message.split("JCAI-")[1].split()[0]
                    issue_key = f"JCAI-{issue_key}"
                    print(f"✓ Created issue: {issue_key}")
                    return issue_key

            else:
                print("✗ Issue creation may have failed")
                print(f"Message: {response_data.get('message', 'No message')}")

        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"✗ Error during request: {str(e)}")

    return None


def test_user_sync_directly():
    """Test user sync service directly"""
    print("\n2. Testing user sync service...")

    # This would require creating a direct endpoint or running sync manually
    # For now, we'll just verify through the issue creation process
    print("User sync will be tested indirectly through issue creation")


def verify_issue_in_jira(issue_key):
    """Verify the issue was created correctly in Jira with assignee"""
    print(f"\n3. Verifying issue {issue_key} in Jira...")

    try:
        # Get issue details
        response = requests.get(
            f"{BASE_URL}/api/multi-user/jira/{USER_ID}/issues/{issue_key}", timeout=30
        )

        if response.status_code == 200:
            issue_data = response.json()
            print(f"✓ Successfully retrieved issue {issue_key}")

            # Check assignee field
            fields = issue_data.get("fields", {})
            assignee = fields.get("assignee")

            if assignee:
                display_name = assignee.get("displayName")
                account_id = assignee.get("accountId")
                print(f"✓ Assignee found: {display_name} (Account ID: {account_id})")

                if display_name and "Anson" in display_name:
                    print("✓ Assignee correctly set to Anson Chan!")
                    return True
                else:
                    print(f"✗ Unexpected assignee: {display_name}")
            else:
                print("✗ No assignee found in issue")

        else:
            print(f"✗ Failed to get issue details: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"✗ Error verifying issue: {str(e)}")

    return False


def run_comprehensive_test():
    """Run the comprehensive assignee test"""
    print("Starting comprehensive assignee functionality test...")
    print(f"Target API: {BASE_URL}")
    print(f"User ID: {USER_ID}")

    # Test issue creation with assignee
    issue_key = test_user_sync_and_assignee()

    if issue_key:
        # Wait a moment for the issue to be fully created
        print("\nWaiting 3 seconds for issue creation to complete...")
        time.sleep(3)

        # Verify the issue
        success = verify_issue_in_jira(issue_key)

        if success:
            print("\n" + "=" * 60)
            print("✓ ASSIGNEE FUNCTIONALITY TEST PASSED!")
            print("  - Issue created successfully")
            print("  - User lookup/sync worked")
            print("  - Assignee field properly set")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("✗ ASSIGNEE FUNCTIONALITY TEST FAILED!")
            print("  - Issue created but assignee not set correctly")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ ASSIGNEE FUNCTIONALITY TEST FAILED!")
        print("  - Issue creation failed")
        print("=" * 60)

    return False


if __name__ == "__main__":
    # Add some helpful debug info
    print("Assignee Functionality Test")
    print("This test will:")
    print("1. Create a Jira issue with an assignee")
    print("2. Verify user lookup and sync works")
    print("3. Check that the assignee field is properly set in Jira")
    print("\nStarting test...\n")

    success = run_comprehensive_test()

    if success:
        print("\n🎉 All tests passed! Assignee functionality is working correctly.")
    else:
        print("\n❌ Tests failed. Please check the logs for details.")

    print("\nTest completed.")
