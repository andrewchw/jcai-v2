#!/usr/bin/env python
"""
Jira Chatbot Extension Diagnostic Tool

This script helps diagnose common issues with the Jira chatbot extension:
1. Multiple OAuth token refresh services
2. Token state inconsistencies
3. Unbounded JQL query issues
4. Connection problems between components

Usage:
python run_diagnostics.py [--fix] [--verbose]

Options:
--fix       Attempt to fix issues automatically
--verbose   Show detailed diagnostic information
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("jira_chatbot_diagnostics.log"),
    ],
)
logger = logging.getLogger(__name__)


class DiagnosticTool:
    def __init__(self, fix_issues=False, verbose=False):
        self.fix_issues = fix_issues
        self.verbose = verbose
        self.issues_found = 0
        self.issues_fixed = 0

        # Paths
        self.server_dir = os.path.dirname(os.path.abspath(__file__))
        self.extension_dir = os.path.join(
            os.path.dirname(self.server_dir), "edge-extension"
        )

        # Files to check
        self.oauth_service_path = os.path.join(
            self.server_dir, "app", "services", "oauth_token_service.py"
        )
        self.background_js_path = os.path.join(
            self.extension_dir, "src", "js", "background.js"
        )
        self.sidebar_js_path = os.path.join(
            self.extension_dir, "src", "js", "sidebar.js"
        )
        self.jira_multi_path = os.path.join(
            self.server_dir, "app", "api", "endpoints", "jira_multi.py"
        )

    def run_diagnostics(self):
        """Run all diagnostic checks."""
        logger.info("Starting Jira chatbot extension diagnostics...")

        self.check_oauth_service()
        self.check_background_js()
        self.check_sidebar_js()
        self.check_jql_queries()
        self.check_token_files()

        # Summary
        logger.info("=" * 50)
        if self.issues_found == 0:
            logger.info(
                "SUCCESS: No issues found! The extension should be working correctly."
            )
        else:
            logger.info(
                f"Found {self.issues_found} issue(s), fixed {self.issues_fixed}."
            )
            if self.issues_found > self.issues_fixed:
                logger.warning(
                    "WARNING - "
                    + str(self.issues_found - self.issues_fixed)
                    + " issue(s) require manual attention."
                )
            else:
                logger.info("✅ All identified issues have been fixed.")

    def check_oauth_service(self):
        """Check for issues in the OAuth token service."""
        logger.info("-" * 50)
        logger.info("Checking OAuth token service...")

        if not os.path.exists(self.oauth_service_path):
            logger.error(f"❌ Could not find OAuth service at {self.oauth_service_path}")
            self.issues_found += 1
            return

        with open(self.oauth_service_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Check for singleton pattern
        if "_refresh_thread_running" not in content:
            logger.error("❌ Multiple token refresh services protection not found!")
            self.issues_found += 1

            if self.fix_issues:
                logger.info(
                    "Attempting to fix multiple token refresh services issue..."
                )
                try:
                    subprocess.run(
                        [
                            "python",
                            os.path.join(
                                self.server_dir, "fix_token_service_direct.py"
                            ),
                        ],
                        check=True,
                        cwd=self.server_dir,
                    )
                    logger.info("✅ Applied fix for multiple token refresh services.")
                    self.issues_fixed += 1
                except subprocess.CalledProcessError:
                    logger.error("Failed to apply token service fix.")
        else:
            logger.info("OK - Token refresh singleton protection is in place.")

        # Check for thread management
        if "OAuthTokenService._refresh_thread_running = False" not in content:
            logger.warning("⚠️ Thread state management may be incomplete.")
            self.issues_found += 1
        else:
            if self.verbose:
                logger.info("✅ Thread state reset code is present.")

    def check_background_js(self):
        """Check for issues in background.js."""
        logger.info("-" * 50)
        logger.info("Checking background.js...")

        if not os.path.exists(self.background_js_path):
            logger.error(f"❌ Could not find background.js at {self.background_js_path}")
            self.issues_found += 1
            return
        with open(self.background_js_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Check for debounce
        if "lastTokenCheckStart" not in content:
            logger.error("❌ Token check debounce protection not found!")
            self.issues_found += 1
        else:
            if self.verbose:
                logger.info("✅ Token check debounce is implemented.")
        # Check for multiple startTokenChecking calls - being more lenient
        start_token_calls = re.findall(r"startTokenChecking\(\)", content)
        if (
            len(start_token_calls) > 6
        ):  # More lenient threshold since calls from different contexts are ok
            logger.warning(
                "WARNING - Excessive calls to startTokenChecking found: "
                + str(len(start_token_calls))
            )
            self.issues_found += 1
        else:
            if self.verbose:
                logger.info(
                    "OK - Appropriate number of startTokenChecking calls found."
                )

        # Check for proper error handling
        if (
            "catch (err) {" not in content
            or "Failed to start token checking interval" not in content
        ):
            logger.warning("⚠️ Error handling in token checking may not be robust.")
            self.issues_found += 1
        else:
            if self.verbose:
                logger.info("✅ Error handling looks good in token checking.")

    def check_sidebar_js(self):
        """Check for issues in sidebar.js."""
        logger.info("-" * 50)
        logger.info("Checking sidebar.js...")

        if not os.path.exists(self.sidebar_js_path):
            logger.error(f"❌ Could not find sidebar.js at {self.sidebar_js_path}")
            self.issues_found += 1
            return

        with open(self.sidebar_js_path, "r", encoding="utf-8") as file:
            content = (
                file.read()
            )  # Check for JQL handling in loadTasks - use a different approach to find the function
        # Look for the function declaration and then search for specific patterns within the file
        if "function loadTasks()" in content:
            # Find the start of the loadTasks function
            load_tasks_start = content.find("function loadTasks()")
            if (
                load_tasks_start != -1
            ):  # Look for the patterns after the function declaration
                after_func = content[
                    load_tasks_start : load_tasks_start + 3000
                ]  # Check first 3000 chars

                if "filters.jql" not in after_func and "jqlBase" not in after_func:
                    logger.error(
                        "ERROR - JQL query construction not found in loadTasks!"
                    )
                    self.issues_found += 1
                elif "updated >=" not in after_func:
                    logger.warning("WARNING - Date restriction for JQL may be missing.")
                    self.issues_found += 1
                elif "assignee = currentUser()" not in after_func:
                    logger.warning("WARNING - User-focused filtering may be missing.")
                    self.issues_found += 1
                else:
                    if self.verbose:
                        logger.info(
                            "OK - JQL query construction looks good in loadTasks."
                        )
            else:
                logger.error("ERROR - loadTasks function structure not found!")
                self.issues_found += 1
        else:
            logger.error("ERROR - Could not find loadTasks function in sidebar.js!")
            self.issues_found += 1

        # Check for debounce mechanisms in token checking
        has_debounce = (
            "lastTokenCheck" in content
            or "timeSinceAuth" in content
            or "lastAuthTime" in content
            or "debounceTime" in content
            or "projectsDebounceTime" in content
        )

        if not has_debounce:
            logger.warning("WARNING - Token check debounce may not be optimal.")
            self.issues_found += 1
        else:
            if self.verbose:
                logger.info("✅ Token check debounce is properly configured.")

        # Check for smart authentication responsiveness
        if "timeSinceAuth < 30000" not in content:
            logger.warning(
                "WARNING - Smart authentication responsiveness may be missing."
            )
            self.issues_found += 1
        else:
            if self.verbose:
                logger.info("✅ Smart authentication responsiveness is implemented.")

    def check_jql_queries(self):
        """Check for JQL query issues in the codebase."""
        logger.info("-" * 50)
        logger.info("Checking JQL query handling...")

        if not os.path.exists(self.jira_multi_path):
            logger.error(f"❌ Could not find jira_multi.py at {self.jira_multi_path}")
            self.issues_found += 1
            return

        with open(self.jira_multi_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Check for JQL restrictions in jira_multi.py
        if "updated >=" not in content:
            logger.error("❌ Date restrictions in JQL queries may be missing!")
            self.issues_found += 1
        else:
            if self.verbose:
                logger.info("✅ Date restrictions found in JQL queries.")

        if "ORDER BY" not in content:
            logger.warning("⚠️ ORDER BY clauses may be missing in JQL queries.")
            self.issues_found += 1
        else:
            if self.verbose:
                logger.info("✅ ORDER BY clauses found in JQL queries.")

    def check_token_files(self):
        """Check for token files and their status."""
        logger.info("-" * 50)
        logger.info("Checking token files...")

        token_file = os.path.join(self.server_dir, "oauth_token.json")
        if os.path.exists(token_file):
            try:
                with open(token_file, "r", encoding="utf-8") as file:
                    token_data = json.load(file)
                # Check token expiration
                expires_at = None
                if "expires_at" in token_data:
                    if isinstance(token_data["expires_at"], str):
                        expires_at = datetime.fromisoformat(
                            token_data["expires_at"].replace("Z", "+00:00")
                        )
                    elif isinstance(token_data["expires_at"], (int, float)):
                        expires_at = datetime.fromtimestamp(token_data["expires_at"])
                elif "expires_in_seconds" in token_data:
                    expires_at = (
                        datetime.now().timestamp() + token_data["expires_in_seconds"]
                    )
                    expires_at = datetime.fromtimestamp(expires_at)

                if expires_at:
                    now = datetime.now()
                    if expires_at < now:
                        logger.warning(
                            f"⚠️ OAuth token is expired! Expired at {expires_at}"
                        )
                        self.issues_found += 1
                    else:
                        time_left = expires_at - now
                        if self.verbose:
                            logger.info(
                                f"✅ OAuth token is valid. Expires in {time_left.total_seconds()/3600:.1f} hours."
                            )
                else:
                    logger.warning("⚠️ Could not determine token expiration.")
                    self.issues_found += 1

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Error parsing oauth_token.json: {str(e)}")
                self.issues_found += 1
        else:
            logger.warning(
                "⚠️ No OAuth token file found. The extension may need authentication."
            )
            self.issues_found += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Jira Chatbot Extension Diagnostic Tool"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix issues automatically"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed diagnostic information"
    )

    args = parser.parse_args()

    try:
        diagnostic_tool = DiagnosticTool(fix_issues=args.fix, verbose=args.verbose)
        diagnostic_tool.run_diagnostics()
    except Exception as e:
        logger.exception(f"Error running diagnostics: {str(e)}")
        sys.exit(1)
