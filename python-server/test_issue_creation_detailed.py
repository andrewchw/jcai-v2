#!/usr/bin/env python3

import asyncio
import os
import sys
import traceback

from app.core.database import get_db
from app.services.multi_user_jira_service import MultiUserJiraService

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


async def test_create_issue():
    """Test the create_issue method with detailed error tracking"""

    try:
        # Create database session
        db = next(get_db())

        # Create MultiUserJiraService with database session
        multi_user_service = MultiUserJiraService(db)

        # Test data
        user_id = "edge-1748270783635-lun5ucqg"
        issue_data = {
            "project_key": "JCAI",
            "summary": "Test issue creation with parameter fix",
            "description": "Testing the fix for create issue method components parameter",
            "issue_type": "Story",
        }

        print("Testing create_issue method with detailed debug...")
        print(f"User ID: {user_id}")
        print(f"Test data: {issue_data}")

        # Test token retrieval first
        try:
            token = multi_user_service.token_service.get_token(user_id, "jira")
            if token:
                print(f"✅ Token found for user {user_id}")
                print(f"Token ID: {token.id}")
                print(f"Token expires at: {token.expires_at}")
            else:
                print(f"❌ No token found for user {user_id}")
                return
        except Exception as e:
            print(f"❌ Error getting token: {e}")
            traceback.print_exc()
            return

        # Test JiraService creation
        try:
            jira_service = multi_user_service.get_jira_service(user_id)
            if jira_service:
                print("✅ JiraService created successfully")
            else:
                print("❌ Failed to create JiraService")
                return
        except Exception as e:
            print(f"❌ Error creating JiraService: {e}")
            traceback.print_exc()
            return

        # Test project access
        try:
            projects = jira_service.get_projects()
            print(f"✅ Retrieved {len(projects)} projects")
            jcai_project = next((p for p in projects if p.get("key") == "JCAI"), None)
            if jcai_project:
                print(f"✅ JCAI project found: {jcai_project.get('name', 'Unknown')}")
            else:
                print("❌ JCAI project not found in available projects")
                print(f"Available projects: {[p.get('key') for p in projects[:5]]}")
        except Exception as e:
            print(f"❌ Error getting projects: {e}")
            traceback.print_exc()

        # Test the actual issue creation
        try:
            result = await multi_user_service.create_issue(user_id, issue_data)

            if result.get("success"):
                print("✅ Issue creation test PASSED")
                print(f"Created issue: {result}")
            else:
                print("❌ Issue creation test FAILED")
                print(f"Error: {result.get('error', 'Unknown error')}")

                # Try to get more details from the JiraService directly
                try:
                    direct_result = jira_service.create_issue(
                        project_key=issue_data["project_key"],
                        summary=issue_data["summary"],
                        description=issue_data["description"],
                        issue_type=issue_data["issue_type"],
                        assignee=None,
                        components=None,
                        additional_fields={},
                    )
                    print(f"Direct JiraService result: {direct_result}")
                except Exception as direct_e:
                    print(f"Direct JiraService error: {direct_e}")
                    traceback.print_exc()

        except Exception as e:
            print(f"❌ Exception during issue creation: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_create_issue())
