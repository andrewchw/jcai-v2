#!/usr/bin/env python3
"""
Jira API Integration Test Script

This script tests various Jira API operations to ensure proper integration:
1. Connectivity test with Jira Cloud
2. Project retrieval functionality
3. Issue search capabilities
4. Issue retrieval and manipulation

Usage:
    python test_jira_api.py
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import services
try:
    from app.services.jira_service import jira_service
    from app.services.oauth_token_service import TokenRefreshEvent
except ImportError:
    logger.error(
        "Failed to import required modules. Make sure you're running from the python-server directory."
    )
    sys.exit(1)


# ANSI color codes
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def clear_screen():
    """Clear terminal screen"""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== {text} ==={Colors.END}\n")


def test_connectivity():
    """Test basic connectivity to Jira Cloud"""
    print_header("Testing Jira Connectivity")

    try:
        is_connected = jira_service.is_connected()
        if is_connected:
            print(f"{Colors.GREEN}✓ Successfully connected to Jira{Colors.END}")

            # Get current user info
            user = jira_service.myself()
            print(
                f"{Colors.GREEN}✓ Logged in as: {user.get('displayName')} ({user.get('emailAddress')}){Colors.END}"
            )
            return True
        else:
            print(f"{Colors.RED}× Failed to connect to Jira{Colors.END}")
            return False
    except Exception as e:
        print(f"{Colors.RED}× Error connecting to Jira: {str(e)}{Colors.END}")
        return False


def test_projects():
    """Test retrieving projects from Jira"""
    print_header("Testing Project Retrieval")

    try:
        projects = jira_service.get_projects()
        if projects:
            print(
                f"{Colors.GREEN}✓ Successfully retrieved {len(projects)} projects{Colors.END}"
            )

            # Display first 5 projects
            print(f"\n{Colors.BOLD}First 5 Projects:{Colors.END}")
            for i, project in enumerate(projects[:5]):
                print(f"  {i+1}. {project['name']} ({project['key']})")

            if len(projects) > 5:
                print(f"  ... and {len(projects) - 5} more")

            return projects
        else:
            print(f"{Colors.YELLOW}! No projects found or empty response{Colors.END}")
            return []
    except Exception as e:
        print(f"{Colors.RED}× Error retrieving projects: {str(e)}{Colors.END}")
        return []


def test_issues(project_key):
    """Test searching for issues in a project"""
    print_header(f"Testing Issue Search for Project '{project_key}'")

    try:
        # Create JQL query for the project
        jql = f"project = {project_key} ORDER BY updated DESC"

        # Search for issues
        issues = jira_service.search_issues(jql, max_results=10)

        # Check if we got issues back
        if issues and "issues" in issues and issues["issues"]:
            issue_list = issues["issues"]
            print(
                f"{Colors.GREEN}✓ Successfully retrieved {len(issue_list)} issues{Colors.END}"
            )

            # Display issues
            print(f"\n{Colors.BOLD}Issues in {project_key}:{Colors.END}")
            for i, issue in enumerate(issue_list):
                fields = issue["fields"]
                status = fields.get("status", {}).get("name", "Unknown")
                assignee = fields.get("assignee", {}).get("displayName", "Unassigned")
                status_color = (
                    Colors.GREEN
                    if status.lower() == "done"
                    else (
                        Colors.YELLOW
                        if status.lower() == "in progress"
                        else Colors.BLUE
                    )
                )
                print(
                    f"  {i+1}. {issue['key']} - {fields.get('summary', 'No summary')} | {status_color}{status}{Colors.END} | Assignee: {assignee}"
                )

            return issues
        else:
            print(
                f"{Colors.YELLOW}! No issues found in project {project_key}{Colors.END}"
            )
            return {}
    except Exception as e:
        print(f"{Colors.RED}× Error retrieving issues: {str(e)}{Colors.END}")
        return {}


def run_tests():
    """Run all Jira API tests"""
    clear_screen()

    print(f"{Colors.BOLD}{Colors.BLUE}JIRA API INTEGRATION TEST{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 50}{Colors.END}")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.BOLD}{'-' * 50}{Colors.END}")

    # Step 1: Test connectivity
    is_connected = test_connectivity()
    if not is_connected:
        print(
            f"\n{Colors.RED}Connectivity test failed. Cannot continue with other tests.{Colors.END}"
        )
        return

    # Step 2: Test retrieving projects
    projects = test_projects()
    if not projects:
        print(
            f"\n{Colors.YELLOW}No projects found. Cannot test issue retrieval.{Colors.END}"
        )
        return

    # Step 3: Test retrieving issues for the first project
    if projects:
        first_project = projects[0]["key"]
        test_issues(first_project)

    print(f"\n{Colors.BOLD}{Colors.GREEN}All tests completed.{Colors.END}")


if __name__ == "__main__":
    # Make sure we have the token
    token = jira_service.get_oauth2_token()
    if not token:
        print(
            f"{Colors.RED}No OAuth token available. Please authenticate first.{Colors.END}"
        )
        sys.exit(1)

    try:
        run_tests()
    except KeyboardInterrupt:
        print("\nTesting interrupted.")
    finally:
        # Cleanup
        if jira_service._token_service:
            jira_service.stop_token_service()
