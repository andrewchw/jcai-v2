"""
Basic Notification Service for Jira Due Date Reminders

This service implements a basic notification system that:
1. Periodically checks for due/overdue Jira tasks
2. Sends browser notifications to users
3. Handles notification responses (Done, Snooze, etc.)
4. Integrates with existing multi-user OAuth system

For Phase 2 implementation (June 16, 2025)
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.core.database import get_db
from app.models.user import User
from app.models.token import OAuthToken
from app.services.multi_user_jira_service import MultiUserJiraService
from app.services.email_service import EmailService
from app.services.jira_notification_service import JiraNotificationService
from app.services.browser_notification_service import get_browser_notification_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class NotificationTask:
    """Represents a task that needs notification"""
    issue_key: str
    summary: str
    assignee: str
    due_date: datetime
    user_id: str
    notification_type: str  # 'due_soon', 'overdue'
    priority: str = 'Medium'


@dataclass
class NotificationPreferences:
    """User notification preferences"""
    enabled: bool = True
    advance_hours: int = 24  # Hours before due date to notify
    check_interval: int = 300  # Seconds between checks


class NotificationService:
    """Service for managing Jira task notifications"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.is_running = False
        self.notification_queue: List[NotificationTask] = []          # Initialize delivery services
        self.email_service = EmailService()
        self.jira_notification_service = JiraNotificationService()
        self.browser_service = get_browser_notification_service()

        # Load configuration from environment
        self.check_interval = int(os.getenv('REMINDER_CHECK_INTERVAL', '300'))
        self.advance_hours = int(os.getenv('NOTIFICATION_ADVANCE_HOURS', '24'))
        self.enabled = os.getenv('NOTIFICATION_ENABLED', 'true').lower() == 'true'
        logger.info(f"NotificationService initialized - enabled: {self.enabled}, "
                   f"check_interval: {self.check_interval}s, advance_hours: {self.advance_hours}h")
        logger.info(f"Email service enabled: {self.email_service.enabled}")
        logger.info(f"Jira notification service enabled: {self.jira_notification_service.enabled}")
        logger.info(f"Browser notification service ready")

    async def start_notification_service(self):
        """Start the background notification service"""
        if not self.enabled:
            logger.info("Notification service is disabled in configuration")
            return

        if self.is_running:
            logger.warning("Notification service is already running")
            return

        logger.info("Starting notification service...")
        self.is_running = True

        while self.is_running:
            try:
                await self._check_due_tasks()
                await self._process_notification_queue()
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in notification service loop: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    def stop_notification_service(self):
        """Stop the background notification service"""
        logger.info("Stopping notification service...")
        self.is_running = False

    async def _check_due_tasks(self):
        """Check for due and overdue tasks for all users"""
        db = self.db_session_factory()
        try:
            # Get all users with valid OAuth tokens
            users = db.query(User).join(OAuthToken).filter(
                OAuthToken.expires_at > datetime.now()            ).all()

            logger.debug(f"Checking due tasks for {len(users)} authenticated users")

            multi_jira_service = MultiUserJiraService(db)

            for user in users:
                try:
                    await self._check_user_due_tasks(user.id, multi_jira_service)
                except Exception as e:
                    logger.error(f"Error checking tasks for user {user.id}: {str(e)}")

        finally:
            db.close()

    async def _check_user_due_tasks(self, user_id: str, multi_jira_service: MultiUserJiraService):
        """Check due tasks for a specific user"""
        jira_service = multi_jira_service.get_jira_service(user_id)

        if not jira_service:
            logger.debug(f"No Jira service available for user {user_id} - no valid token found")
            return

        try:
            # Calculate date range for due soon notifications
            now = datetime.now()
            due_soon_date = now + timedelta(hours=self.advance_hours)

            # JQL to find tasks due soon or overdue, assigned to current user
            jql_due_soon = f"""
                assignee = currentUser() AND
                due >= "{now.strftime('%Y-%m-%d')}" AND
                due <= "{due_soon_date.strftime('%Y-%m-%d')}" AND
                status != Done AND status != Closed AND status != Resolved
                ORDER BY due ASC
            """

            jql_overdue = f"""
                assignee = currentUser() AND
                due < "{now.strftime('%Y-%m-%d')}" AND
                status != Done AND status != Closed AND status != Resolved
                ORDER BY due ASC
            """

            # Get due soon tasks
            due_soon_tasks = jira_service.search_issues(jql_due_soon, max_results=50)
            for task in due_soon_tasks.get('issues', []):
                await self._add_notification_task(task, user_id, 'due_soon')

            # Get overdue tasks
            overdue_tasks = jira_service.search_issues(jql_overdue, max_results=50)
            for task in overdue_tasks.get('issues', []):
                await self._add_notification_task(task, user_id, 'overdue')

            logger.debug(f"User {user_id}: {len(due_soon_tasks.get('issues', []))} due soon, "
                        f"{len(overdue_tasks.get('issues', []))} overdue")

        except Exception as e:
            logger.error(f"Error searching for due tasks for user {user_id}: {str(e)}")

    async def _add_notification_task(self, jira_issue: Dict, user_id: str, notification_type: str):
        """Add a task to the notification queue"""
        try:
            # Extract due date
            due_date_str = jira_issue.get('fields', {}).get('duedate')
            if not due_date_str:
                return

            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')

            # Check if we already have a notification for this task
            issue_key = jira_issue.get('key')
            existing = next((n for n in self.notification_queue
                           if n.issue_key == issue_key and n.user_id == user_id), None)

            if existing:
                logger.debug(f"Notification for {issue_key} already queued for user {user_id}")
                return            # Ensure issue_key is valid
            if not issue_key:
                logger.warning(f"Skipping notification creation - invalid issue key: {issue_key}")
                return

            # Create notification task
            notification_task = NotificationTask(
                issue_key=issue_key,
                summary=jira_issue.get('fields', {}).get('summary', 'No summary'),
                assignee=user_id,
                due_date=due_date,
                user_id=user_id,
                notification_type=notification_type,
                priority=jira_issue.get('fields', {}).get('priority', {}).get('name', 'Medium')
            )

            self.notification_queue.append(notification_task)
            logger.info(f"Added {notification_type} notification for {issue_key} (user: {user_id})")

        except Exception as e:
            logger.error(f"Error creating notification task: {str(e)}")

    async def _process_notification_queue(self):
        """Process queued notifications"""
        if not self.notification_queue:
            return

        logger.info(f"Processing {len(self.notification_queue)} queued notifications")

        # Process notifications in batches to avoid overwhelming users
        batch_size = 3  # Max 3 notifications per cycle
        batch = self.notification_queue[:batch_size]
        self.notification_queue = self.notification_queue[batch_size:]

        for notification in batch:
            try:
                await self._send_notification(notification)
            except Exception as e:
                logger.error(f"Error sending notification for {notification.issue_key}: {str(e)}")

    async def _send_notification(self, notification: NotificationTask):
        """Send both Jira native and browser notifications"""
        try:
            # Get user details for email
            db = self.db_session_factory()
            multi_jira_service = None
            jira_service = None
            try:
                user = db.query(User).filter(User.id == notification.user_id).first()
                user_email = getattr(user, 'email', None) if user else None

                # Get Jira service for this user
                multi_jira_service = MultiUserJiraService(db)
                jira_service = multi_jira_service.get_jira_service(notification.user_id)
            finally:
                db.close()

            # Create issue data structure for services
            issue_data = {
                'key': notification.issue_key,
                'fields': {
                    'summary': notification.summary,
                    'duedate': notification.due_date.strftime('%Y-%m-%d'),
                    'assignee': {'displayName': notification.assignee},
                    'priority': {'name': notification.priority},
                    'status': {'name': 'In Progress'}  # Default status
                }
            }

            # Send browser notification
            browser_notification = self.browser_service.create_due_date_notification(
                issue_data,
                notification.notification_type,
                notification.user_id
            )
            self.browser_service.queue_notification(browser_notification)

            # Send notification using preferred method
            jira_notification_sent = False
            email_sent = False

            # Try Jira native notification first (preferred method)
            if jira_service and self.jira_notification_service.enabled:
                jira_notification_sent = await self.jira_notification_service.send_due_date_reminder(
                    notification.user_id,
                    jira_service,
                    issue_data,
                    notification.notification_type
                )
                if jira_notification_sent:
                    logger.info(f"✅ Jira native notification sent for {notification.issue_key}")

            # Fallback to email if Jira notification failed and user has email
            if not jira_notification_sent and user_email and self.email_service.enabled:
                email_sent = await self.email_service.send_due_date_reminder(
                    user_email,
                    issue_data,
                    notification.notification_type
                )
                if email_sent:
                    logger.info(f"📧 Email notification sent as fallback for {notification.issue_key}")

            # Log the result
            days_until_due = (notification.due_date - datetime.now()).days
            if notification.notification_type == 'overdue':
                days_overdue = abs(days_until_due)
                message = f"⚠️ OVERDUE: {notification.summary} (#{notification.issue_key}) - {days_overdue} days overdue"
            else:
                if days_until_due == 0:
                    message = f"🔔 DUE TODAY: {notification.summary} (#{notification.issue_key})"
                elif days_until_due == 1:
                    message = f"📅 Due tomorrow: {notification.summary} (#{notification.issue_key})"
                else:
                    message = f"📅 Due in {days_until_due} days: {notification.summary} (#{notification.issue_key})"

            delivery_status = []
            if jira_notification_sent:
                delivery_status.append("jira-native")
            if email_sent:
                delivery_status.append("email")
            delivery_status.append("browser")

            logger.info(f"NOTIFICATION SENT [{notification.user_id}] via {', '.join(delivery_status)}: {message}")

        except Exception as e:
            logger.error(f"Error sending notification for {notification.issue_key}: {str(e)}")

    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification service statistics"""
        return {
            'is_running': self.is_running,
            'queue_length': len(self.notification_queue),
            'check_interval': self.check_interval,
            'advance_hours': self.advance_hours,
            'enabled': self.enabled
        }

    async def handle_notification_response(self, user_id: str, issue_key: str, action: str):
        """Handle user response to a notification"""
        logger.info(f"Notification response: user {user_id}, issue {issue_key}, action {action}")

        if action == 'done':
            # Mark task as done in Jira
            db = self.db_session_factory()
            try:
                multi_jira_service = MultiUserJiraService(db)
                jira_service = multi_jira_service.get_jira_service(user_id)

                if jira_service:
                    # Transition issue to Done status
                    result = jira_service.transition_issue(issue_key, 'Done')
                    logger.info(f"Marked {issue_key} as Done for user {user_id}: {result}")

            except Exception as e:
                logger.error(f"Error marking {issue_key} as done: {str(e)}")
            finally:
                db.close()

        elif action == 'snooze':
            # Remove from queue and re-add later (simple snooze)
            self.notification_queue = [n for n in self.notification_queue
                                     if not (n.issue_key == issue_key and n.user_id == user_id)]
            logger.info(f"Snoozed notification for {issue_key} (user: {user_id})")

        # TODO: Add more actions like 'view', 'update', etc.


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(db_session_factory) -> NotificationService:
    """Get or create the global notification service instance"""
    global _notification_service

    if _notification_service is None:
        _notification_service = NotificationService(db_session_factory)

    return _notification_service


async def start_notification_service(db_session_factory):
    """Start the global notification service"""
    service = get_notification_service(db_session_factory)
    await service.start_notification_service()


def stop_notification_service():
    """Stop the global notification service"""
    global _notification_service

    if _notification_service:
        _notification_service.stop_notification_service()
