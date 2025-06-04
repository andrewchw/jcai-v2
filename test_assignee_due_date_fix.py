"""
Test the complete assignee and due date fix for issue creation
"""
import asyncio
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), "python-server"))

from app.core.database import SessionLocal
from app.services.multi_user_jira_service import MultiUserJiraService


async def test_create_issue_with_assignee_and_due_date():
    """Test creating an issue with assignee lookup and due date"""

    print("🧪 Testing complete assignee lookup and due date fix...")

    try:
        # Initialize database session
        db = SessionLocal()

        # Initialize service
        multi_user_service = MultiUserJiraService(db)

        # Test user
        user_id = "edge-1748270783635-lun5ucqg"

        # Test 1: Issue with accountId assignee (fixed format)
        print("\n📋 Test 1: Issue with accountId assignee")
        issue_data_with_account_id = {
            "project": {"key": "JCAI"},
            "summary": "Test issue with accountId assignee and due date",
            "description": "Testing the complete fix for assignee and due date handling",
            "issuetype": {"name": "Task"},
            "assignee": {
                "accountId": "6136b985c425a20068f11c8c"
            },  # Anson Chan's account ID
            "duedate": "2025-01-03",  # Tomorrow's date
            "priority": {"name": "High"},
        }

        result1 = await multi_user_service.create_issue(
            user_id, issue_data_with_account_id
        )

        if result1.get("success"):
            print(f"✅ Test 1 PASSED: Issue created successfully")
            print(f"   Issue key: {result1['issue']['key']}")
            print(f"   Issue data: {result1['issue']}")
        else:
            print(f"❌ Test 1 FAILED: {result1.get('error', 'Unknown error')}")

        # Test 2: Issue with name assignee (fallback format)
        print("\n📋 Test 2: Issue with name assignee (fallback)")
        issue_data_with_name = {
            "project": {"key": "JCAI"},
            "summary": "Test issue with name assignee and due date",
            "description": "Testing the fallback name assignee handling",
            "issuetype": {"name": "Task"},
            "assignee": {"name": "Anson Chan"},  # Display name fallback
            "duedate": "2025-01-04",  # Day after tomorrow
            "priority": {"name": "Medium"},
        }

        result2 = await multi_user_service.create_issue(user_id, issue_data_with_name)

        if result2.get("success"):
            print(f"✅ Test 2 PASSED: Issue created successfully")
            print(f"   Issue key: {result2['issue']['key']}")
        else:
            print(f"❌ Test 2 FAILED: {result2.get('error', 'Unknown error')}")

        # Test 3: Issue without assignee or due date (basic test)
        print("\n📋 Test 3: Issue without assignee or due date")
        issue_data_basic = {
            "project": {"key": "JCAI"},
            "summary": "Test issue without assignee or due date",
            "description": "Testing basic issue creation",
            "issuetype": {"name": "Task"},
        }

        result3 = await multi_user_service.create_issue(user_id, issue_data_basic)

        if result3.get("success"):
            print(f"✅ Test 3 PASSED: Basic issue created successfully")
            print(f"   Issue key: {result3['issue']['key']}")
        else:
            print(f"❌ Test 3 FAILED: {result3.get('error', 'Unknown error')}")

        # Summary
        print("\n📊 Test Summary:")
        tests_passed = sum(
            [
                result1.get("success", False),
                result2.get("success", False),
                result3.get("success", False),
            ]
        )
        print(f"   Tests passed: {tests_passed}/3")

        if tests_passed == 3:
            print(
                "🎉 All tests passed! The assignee and due date fix is working correctly."
            )
        elif tests_passed > 0:
            print("⚠️ Some tests passed. The fix is partially working.")
        else:
            print("💥 All tests failed. The fix needs more work.")

        return tests_passed == 3

    except Exception as e:
        print(f"❌ ERROR during testing: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = asyncio.run(test_create_issue_with_assignee_and_due_date())
    print(f"\n🏁 Test completed. Success: {success}")
