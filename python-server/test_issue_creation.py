#!/usr/bin/env python3
"""
Test script to verify the create_issue parameter fix
"""
import asyncio
import os
import sys

sys.path.append(".")


async def test_create_issue():
    from app.core.database import SessionLocal
    from app.services.multi_user_jira_service import MultiUserJiraService

    # Initialize database session
    db = SessionLocal()

    try:
        # Initialize service with database session
        multi_user_service = MultiUserJiraService(db)
        user_id = "edge-1748270783635-lun5ucqg"

        try:
            print("Testing create_issue method...")
            result = await multi_user_service.create_issue(
                user_id=user_id,
                project_key="TEST",
                summary="Test issue creation",
                description="Testing the fix for create issue method",
                issue_type="Task",
                assignee=None,
                additional_fields={},
            )
            print("SUCCESS: Issue creation completed")
            print("Result:", result)
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback

            traceback.print_exc()
            return False
    finally:
        db.close()


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_create_issue())
    if success:
        print("✅ Create issue test PASSED")
    else:
        print("❌ Create issue test FAILED")
