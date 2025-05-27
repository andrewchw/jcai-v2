#!/usr/bin/env python3
"""
Test to verify that the components parameter fix is working.
This tests the method signature without authentication issues.
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.jira_service import JiraService


def test_components_parameter():
    """Test that JiraService.create_issue accepts the components parameter"""

    print("Testing JiraService.create_issue method signature...")

    # Create a dummy JiraService instance (won't initialize properly without tokens, but that's fine)
    try:
        # We're just testing the method signature, not actually calling it
        jira_service = JiraService(
            token_dict={
                "access_token": "dummy",
                "refresh_token": "dummy",
                "cloud_id": "dummy",
            }
        )

        # Check if the create_issue method exists and has the right parameters
        import inspect

        sig = inspect.signature(jira_service.create_issue)
        params = list(sig.parameters.keys())

        print(f"✅ Method parameters: {params}")

        # Check that all expected parameters are present
        expected_params = [
            "project_key",
            "summary",
            "description",
            "issue_type",
            "assignee",
            "components",
            "additional_fields",
        ]

        missing_params = [param for param in expected_params if param not in params]
        if missing_params:
            print(f"❌ Missing parameters: {missing_params}")
            return False

        # Check that 'components' parameter is present
        if "components" in params:
            print("✅ 'components' parameter is present in create_issue method")
        else:
            print("❌ 'components' parameter is missing from create_issue method")
            return False

        print("✅ Parameter signature test PASSED")
        return True

    except Exception as e:
        print(f"❌ Error testing method signature: {e}")
        return False


if __name__ == "__main__":
    success = test_components_parameter()
    if success:
        print("\n🎉 CONCLUSION: The components parameter fix is working correctly!")
        print(
            "The original 'unexpected keyword argument components' error has been resolved."
        )
    else:
        print("\n❌ CONCLUSION: There are still issues with the method signature.")
