"""Browser notification service for real-time Jira task notifications."""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BrowserNotification:
    """Browser notification data structure"""
    id: str
    title: str
    body: str
    icon: str
    badge: str
    tag: str
    requireInteraction: bool = False
    silent: bool = False
    actions: Optional[List[Dict[str, str]]] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.actions is None:
            self.actions = []
        if self.data is None:
            self.data = {}


class BrowserNotificationService:
    """Service for managing browser notifications for Jira tasks"""

    def __init__(self):
        self.pending_notifications: List[BrowserNotification] = []
        logger.info("Browser notification service initialized")

    def create_due_date_notification(self, issue_data: Dict[str, Any],
                                   notification_type: str = 'due_soon',
                                   user_id: Optional[str] = None) -> BrowserNotification:
        """Create a browser notification for due date reminders"""

        fields = issue_data.get('fields', {})
        issue_key = issue_data.get('key', 'Unknown')
        summary = fields.get('summary', 'No summary')
        due_date = fields.get('duedate', 'No due date')
        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned')

        # Generate notification content based on type
        if notification_type == 'overdue':
            title = f"🚨 OVERDUE: {issue_key}"
            body = f"{summary}\nDue: {due_date} | Assignee: {assignee}"
            icon = "/static/icons/notification-overdue.png"
            badge = "/static/icons/badge-overdue.png"
            tag = f"overdue_{issue_key}"
            require_interaction = True
        elif notification_type == 'due_soon':
            title = f"⏰ Due Soon: {issue_key}"
            body = f"{summary}\nDue: {due_date} | Assignee: {assignee}"
            icon = "/static/icons/notification-due.png"
            badge = "/static/icons/badge-due.png"
            tag = f"due_soon_{issue_key}"
            require_interaction = False
        else:
            title = f"📋 Jira Reminder: {issue_key}"
            body = f"{summary}\nDue: {due_date} | Assignee: {assignee}"
            icon = "/static/icons/notification-general.png"
            badge = "/static/icons/badge-general.png"
            tag = f"reminder_{issue_key}"
            require_interaction = False

        # Create notification actions
        actions = [
            {
                "action": "view",
                "title": "View in Jira",
                "icon": "/static/icons/action-view.png"
            },
            {
                "action": "snooze",
                "title": "Snooze 1 hour",
                "icon": "/static/icons/action-snooze.png"
            }
        ]

        # Additional data for handling clicks
        notification_data = {
            "issue_key": issue_key,
            "issue_url": f"{self._get_jira_url()}/browse/{issue_key}",
            "notification_type": notification_type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }

        notification = BrowserNotification(
            id=f"{notification_type}_{issue_key}_{datetime.now().timestamp()}",
            title=title,
            body=body,
            icon=icon,
            badge=badge,
            tag=tag,
            requireInteraction=require_interaction,
            actions=actions,
            data=notification_data
        )

        return notification

    def queue_notification(self, notification: BrowserNotification) -> None:
        """Add notification to the pending queue"""
        # Remove any existing notifications with the same tag
        self.pending_notifications = [
            n for n in self.pending_notifications
            if n.tag != notification.tag
        ]

        # Add new notification
        self.pending_notifications.append(notification)
        logger.info(f"Queued browser notification: {notification.title}")

    def get_pending_notifications(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pending notifications for a user"""
        notifications = self.pending_notifications

        if user_id:
            notifications = [
                n for n in notifications
                if n.data.get('user_id') == user_id
            ]

        return [asdict(n) for n in notifications]

    def mark_notification_sent(self, notification_id: str) -> bool:
        """Mark a notification as sent and remove from queue"""
        initial_count = len(self.pending_notifications)
        self.pending_notifications = [
            n for n in self.pending_notifications
            if n.id != notification_id
        ]

        sent = len(self.pending_notifications) < initial_count
        if sent:
            logger.info(f"Marked notification {notification_id} as sent")

        return sent

    def clear_notifications_for_issue(self, issue_key: str) -> int:
        """Clear all notifications for a specific issue"""
        initial_count = len(self.pending_notifications)
        self.pending_notifications = [
            n for n in self.pending_notifications
            if n.data.get('issue_key') != issue_key
        ]

        cleared_count = initial_count - len(self.pending_notifications)
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} notifications for issue {issue_key}")

        return cleared_count

    def create_test_notification(self, user_id: str) -> BrowserNotification:
        """Create a test notification for testing purposes"""
        test_issue = {
            'key': 'TEST-123',
            'fields': {
                'summary': 'Test notification for browser alerts',
                'duedate': '2025-06-17',
                'assignee': {'displayName': 'Test User'},
                'status': {'name': 'In Progress'},
                'priority': {'name': 'High'}
            }
        }

        return self.create_due_date_notification(
            test_issue,
            'due_soon',
            user_id
        )

    def _get_jira_url(self) -> str:
        """Get Jira URL from environment or use default"""
        import os
        return os.getenv('JIRA_URL', 'https://your-domain.atlassian.net')

    def get_notification_stats(self) -> Dict[str, Any]:
        """Get statistics about pending notifications"""
        total = len(self.pending_notifications)
        by_type: Dict[str, int] = {}
        by_tag: Dict[str, int] = {}

        for notification in self.pending_notifications:
            notification_type = notification.data.get('notification_type', 'unknown')
            by_type[notification_type] = by_type.get(notification_type, 0) + 1

            tag_prefix = notification.tag.split('_')[0] if '_' in notification.tag else notification.tag
            by_tag[tag_prefix] = by_tag.get(tag_prefix, 0) + 1

        return {
            "total_pending": total,
            "by_type": by_type,
            "by_tag": by_tag,
            "oldest_notification": (
                min(self.pending_notifications, key=lambda n: n.timestamp).timestamp
                if self.pending_notifications else None
            )
        }


# Singleton instance
_browser_notification_service = None

def get_browser_notification_service() -> BrowserNotificationService:
    """Get the singleton browser notification service instance"""
    global _browser_notification_service
    if _browser_notification_service is None:
        _browser_notification_service = BrowserNotificationService()
    return _browser_notification_service
