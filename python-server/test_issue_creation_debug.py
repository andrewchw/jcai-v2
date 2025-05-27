# Test Create Issue Fix with Debug
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.db_token_service import DBTokenService
from app.services.multi_user_jira_service import MultiUserJiraService


async def test_create_issue():
    print("Testing create_issue method with debug...")

    try:  # Initialize the services
        db = SessionLocal()
        multi_user_service = MultiUserJiraService(db)

        # Test data using JCAI project
        issue_data = {
            "project_key": "JCAI",
            "summary": "Test issue creation with parameter fix",
            "description": "Testing the fix for create issue method components parameter",
            "issue_type": "Story",
        }

        print(f"Test data: {issue_data}")

        # Test user from database
        user_id = "edge-1748270783635-lun5ucqg"

        # Try to create issue
        result = await multi_user_service.create_issue(user_id, issue_data)

        print(f"Result: {result}")

        if result.get("success"):
            print("✅ Create issue test PASSED")
            print(f"Created issue: {result.get('issue', {})}")
        else:
            print("❌ Create issue test FAILED")
            print(f"Error: {result.get('error', 'No error message')}")
            # Let's also try to get more details by checking the token
            try:
                tokens = multi_user_service.token_service.get_token(user_id, "jira")
                if tokens:
                    print(
                        f"User has tokens: access_token present: {bool(tokens.access_token)}"
                    )
                    print(f"Tokens expire at: {tokens.expires_at}")
                else:
                    print("No tokens found for user")
            except Exception as token_error:
                print(f"Error checking tokens: {token_error}")

        db.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_create_issue())
