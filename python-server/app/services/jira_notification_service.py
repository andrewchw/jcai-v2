"""
Jira Cloud Native Notification Service

This service uses Jira Cloud's native notification API instead of SMTP
to send email notifications about due date reminders. This approach is
better because:

1. No SMTP credentials needed
2. Uses the user's existing Jira Cloud account
3. Notifications appear in Jira's notification system
4. Consistent with Jira's native email formatting
5. Respects user's Jira notification preferences

API: POST /rest/api/3/issue/{issueIdOrKey}/notify
"""

import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class JiraNotificationService:
    """Service for sending notifications through Jira Cloud's native notification API"""

    def __init__(self):
        self.enabled = True
        logger.info("Jira Cloud notification service initialized")

    async def send_due_date_reminder(
        self,
        user_id: str,
        jira_service,
        issue_data: Dict[str, Any],
        notification_type: str
    ) -> bool:
        """
        Send a due date reminder notification using Jira's native notification API

        Args:
            user_id: The user to send notification to
            jira_service: The JiraService instance with OAuth token
            issue_data: Issue data from Jira API
            notification_type: 'due_soon' or 'overdue'

        Returns:
            bool: True if notification was sent successfully
        """
        try:
            issue_key = issue_data.get('key')
            if not issue_key:
                logger.error("No issue key provided for notification")
                return False
              # Get user info for targeted notification
            user_info = jira_service.myself()
            if not user_info:
                logger.error(f"Could not get user info for notification targeting")
                return False

            user_account_id = user_info.get('accountId')
            if not user_account_id:
                logger.error("Could not get user account ID for notification")
                return False

            # Create notification message based on type
            message = self._create_notification_message(issue_data, notification_type)

            # Create notification payload for Jira API
            notification_payload = {
                "subject": self._create_subject(issue_data, notification_type),
                "textBody": message,
                "htmlBody": self._create_html_message(issue_data, notification_type),
                "to": {
                    "users": [
                        {
                            "accountId": user_account_id
                        }
                    ]
                }
            }

            # Send notification via Jira API
            success = jira_service.send_issue_notification(issue_key, notification_payload)

            if success:
                logger.info(f"Jira notification sent successfully for {issue_key} to user {user_id}")
                return True
            else:
                logger.error(f"Failed to send Jira notification for {issue_key}")
                return False

        except Exception as e:
            logger.error(f"Error sending Jira notification: {str(e)}")
            return False

    def _create_subject(self, issue_data: Dict[str, Any], notification_type: str) -> str:
        """Create email subject line"""
        issue_key = issue_data.get('key', 'Unknown')
        summary = issue_data.get('fields', {}).get('summary', 'No summary')

        if notification_type == 'overdue':
            return f"⚠️ OVERDUE: {summary} ({issue_key})"
        elif notification_type == 'due_today':
            return f"🔔 DUE TODAY: {summary} ({issue_key})"
        else:
            return f"📅 Due Soon: {summary} ({issue_key})"

    def _create_notification_message(self, issue_data: Dict[str, Any], notification_type: str) -> str:
        """Create plain text notification message"""
        issue_key = issue_data.get('key', 'Unknown')
        summary = issue_data.get('fields', {}).get('summary', 'No summary')
        due_date_str = issue_data.get('fields', {}).get('duedate', 'No due date')
        priority = issue_data.get('fields', {}).get('priority', {}).get('name', 'Medium')

        # Calculate days until/past due
        if due_date_str and due_date_str != 'No due date':
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                days_diff = (due_date - datetime.now()).days

                if notification_type == 'overdue':
                    days_overdue = abs(days_diff)
                    urgency_text = f"This task is {days_overdue} day{'s' if days_overdue != 1 else ''} overdue!"
                elif days_diff == 0:
                    urgency_text = "This task is due TODAY!"
                elif days_diff == 1:
                    urgency_text = "This task is due TOMORROW!"
                else:
                    urgency_text = f"This task is due in {days_diff} days."
            except:
                urgency_text = "Please check the due date."
        else:
            urgency_text = "Due date information is not available."

        message = f"""Jira Due Date Reminder

{urgency_text}

Issue: {issue_key}
Summary: {summary}
Priority: {priority}
Due Date: {due_date_str}

Please review this issue and take appropriate action.

This notification was sent by your Jira Chatbot Extension."""

        return message

    def _create_html_message(self, issue_data: Dict[str, Any], notification_type: str) -> str:
        """Create HTML notification message"""
        issue_key = issue_data.get('key', 'Unknown')
        summary = issue_data.get('fields', {}).get('summary', 'No summary')
        due_date_str = issue_data.get('fields', {}).get('duedate', 'No due date')
        priority = issue_data.get('fields', {}).get('priority', {}).get('name', 'Medium')

        # Calculate days until/past due
        urgency_color = "#FF6B6B"  # Red for overdue
        urgency_icon = "⚠️"

        if due_date_str and due_date_str != 'No due date':
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                days_diff = (due_date - datetime.now()).days

                if notification_type == 'overdue':
                    days_overdue = abs(days_diff)
                    urgency_text = f"This task is <strong>{days_overdue} day{'s' if days_overdue != 1 else ''} overdue!</strong>"
                    urgency_color = "#FF4757"  # Bright red
                    urgency_icon = "⚠️"
                elif days_diff == 0:
                    urgency_text = "This task is <strong>due TODAY!</strong>"
                    urgency_color = "#FF6348"  # Orange-red
                    urgency_icon = "🔔"
                elif days_diff == 1:
                    urgency_text = "This task is <strong>due TOMORROW!</strong>"
                    urgency_color = "#FFA726"  # Orange
                    urgency_icon = "📅"
                else:
                    urgency_text = f"This task is due in <strong>{days_diff} days</strong>."
                    urgency_color = "#4ECDC4"  # Teal
                    urgency_icon = "📅"
            except:
                urgency_text = "Please check the due date."
                urgency_color = "#95A5A6"  # Gray
        else:
            urgency_text = "Due date information is not available."
            urgency_color = "#95A5A6"  # Gray

        # Determine priority color
        priority_colors = {
            'Highest': '#FF4757',
            'High': '#FF6348',
            'Medium': '#FFA726',
            'Low': '#4ECDC4',
            'Lowest': '#95A5A6'
        }
        priority_color = priority_colors.get(priority, '#FFA726')

        html_message = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, {urgency_color}, {urgency_color}dd); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px; font-weight: 600;">
                    {urgency_icon} Jira Due Date Reminder
                </h1>
            </div>

            <!-- Content -->
            <div style="padding: 30px;">
                <!-- Urgency Message -->
                <div style="background: {urgency_color}15; border: 2px solid {urgency_color}; border-radius: 8px; padding: 15px; margin-bottom: 25px; text-align: center;">
                    <p style="margin: 0; font-size: 18px; color: {urgency_color}; font-weight: 600;">
                        {urgency_text}
                    </p>
                </div>

                <!-- Issue Details -->
                <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 20px;">Issue Details</h3>

                    <div style="margin-bottom: 12px;">
                        <span style="font-weight: 600; color: #555; display: inline-block; width: 80px;">Issue:</span>
                        <span style="background: #e74c3c; color: white; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-family: monospace;">
                            {issue_key}
                        </span>
                    </div>

                    <div style="margin-bottom: 12px;">
                        <span style="font-weight: 600; color: #555; display: inline-block; width: 80px;">Summary:</span>
                        <span style="color: #2c3e50; font-weight: 500;">{summary}</span>
                    </div>

                    <div style="margin-bottom: 12px;">
                        <span style="font-weight: 600; color: #555; display: inline-block; width: 80px;">Priority:</span>
                        <span style="background: {priority_color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: 600;">
                            {priority}
                        </span>
                    </div>

                    <div style="margin-bottom: 0;">
                        <span style="font-weight: 600; color: #555; display: inline-block; width: 80px;">Due Date:</span>
                        <span style="color: {urgency_color}; font-weight: 600;">{due_date_str}</span>
                    </div>
                </div>

                <!-- Action Message -->
                <div style="text-align: center; padding: 20px; background: #f1f2f6; border-radius: 8px;">
                    <p style="margin: 0; color: #2c3e50; font-size: 16px;">
                        Please review this issue and take appropriate action.
                    </p>
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 0 0 10px 10px; text-align: center; border-top: 1px solid #e9ecef;">
                <p style="margin: 0; color: #6c757d; font-size: 12px;">
                    This notification was sent by your Jira Chatbot Extension
                </p>
            </div>
        </div>        """

        return html_message

    async def test_notification(self, user_id: str, jira_service) -> Dict[str, Any]:
        """Test the notification service"""
        try:
            # Get the actual issue from Jira API
            issue_key = 'JCAI-124'
            issue_data = jira_service.get_issue(issue_key)

            if not issue_data:
                return {
                    "success": False,
                    "message": f"Could not retrieve issue {issue_key}",
                    "service": "Jira Cloud Native API",
                    "method": "Issue Retrieval"
                }

            logger.info(f"Retrieved issue data for {issue_key}: {issue_data.get('key', 'No key')}")

            success = await self.send_due_date_reminder(
                user_id,
                jira_service,
                issue_data,
                'due_today'
            )

            return {
                "success": success,
                "message": "Test notification sent via Jira Cloud API" if success else "Failed to send test notification",
                "service": "Jira Cloud Native API",
                "method": "Jira Issue Notification API"
            }

        except Exception as e:
            logger.error(f"Error testing Jira notification service: {str(e)}")
            return {
                "success": False,
                "message": f"Test failed: {str(e)}",
                "service": "Jira Cloud Native API",
                "method": "Error"
            }
