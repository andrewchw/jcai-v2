"""
API endpoints for the notification system
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.services.notification_service import get_notification_service
from app.services.email_service import EmailService
from app.services.browser_notification_service import get_browser_notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """Response model for notification actions"""
    success: bool
    message: str
    action: str
    issue_key: str


class NotificationStats(BaseModel):
    """Notification service statistics"""
    is_running: bool
    queue_length: int
    check_interval: int
    advance_hours: int
    enabled: bool


class EmailTestRequest(BaseModel):
    """Request model for testing email notifications"""
    user_email: str
    test_type: str = "due_soon"  # due_soon, overdue, general


class BrowserNotificationList(BaseModel):
    """Response model for browser notifications"""
    notifications: list
    total_count: int


@router.get("/status", response_model=NotificationStats)
async def get_notification_status(db: Session = Depends(get_db)):
    """Get notification service status and statistics"""
    try:
        service = get_notification_service(lambda: db)
        stats = service.get_notification_stats()
        return NotificationStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notification status: {str(e)}")


@router.post("/respond/{user_id}", response_model=NotificationResponse)
async def handle_notification_response(
    user_id: str,
    issue_key: str = Query(..., description="Jira issue key"),
    action: str = Query(..., description="Action: done, snooze, view"),
    db: Session = Depends(get_db)
):
    """Handle user response to a notification"""
    try:
        service = get_notification_service(lambda: db)
        await service.handle_notification_response(user_id, issue_key, action)

        return NotificationResponse(
            success=True,
            message=f"Successfully processed {action} action for {issue_key}",
            action=action,
            issue_key=issue_key
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error handling notification response: {str(e)}"
        )


@router.post("/test/{user_id}")
async def test_notification_check(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Test notification checking for a specific user (development endpoint)"""
    try:
        from app.services.multi_user_jira_service import MultiUserJiraService

        service = get_notification_service(lambda: db)
        multi_jira_service = MultiUserJiraService(db)

        # Force a check for this user
        await service._check_user_due_tasks(user_id, multi_jira_service)

        return {
            "success": True,
            "message": f"Notification check completed for user {user_id}",
            "queue_length": len(service.notification_queue)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing notifications: {str(e)}"
        )


@router.get("/queue")
async def get_notification_queue(db: Session = Depends(get_db)):
    """Get current notification queue (development endpoint)"""
    try:
        service = get_notification_service(lambda: db)

        queue_data = []
        for notification in service.notification_queue:
            queue_data.append({
                "issue_key": notification.issue_key,
                "summary": notification.summary,
                "user_id": notification.user_id,
                "due_date": notification.due_date.isoformat(),
                "notification_type": notification.notification_type,
                "priority": notification.priority
            })

        return {
            "queue_length": len(queue_data),
            "notifications": queue_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting notification queue: {str(e)}"
        )


@router.get("/email/test-config")
async def test_email_configuration():
    """Test email service configuration"""
    try:
        email_service = EmailService()
        result = email_service.test_email_config()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing email config: {str(e)}")


@router.post("/email/send-test")
async def send_test_email(request: EmailTestRequest):
    """Send a test email notification"""
    try:
        email_service = EmailService()

        if not email_service.enabled:
            raise HTTPException(status_code=400, detail="Email service is not configured")
          # Create test issue data
        test_issue = {
            'key': 'TEST-EMAIL',
            'fields': {
                'summary': f'Test Email Notification ({request.test_type})',
                'duedate': '2025-06-17',
                'assignee': {'displayName': 'Test User'},
                'status': {'name': 'In Progress'},
                'priority': {'name': 'High'}
            }
        }

        success = await email_service.send_due_date_reminder(
            request.user_email,
            test_issue,
            request.test_type
        )

        if success:
            return {"success": True, "message": f"Test email sent to {request.user_email}"}
        else:
            return {"success": False, "message": "Failed to send test email"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending test email: {str(e)}")


@router.get("/browser/pending/{user_id}", response_model=BrowserNotificationList)
async def get_pending_browser_notifications(user_id: str):
    """Get pending browser notifications for a user"""
    try:
        browser_service = get_browser_notification_service()
        notifications = browser_service.get_pending_notifications(user_id)

        return BrowserNotificationList(
            notifications=notifications,
            total_count=len(notifications)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notifications: {str(e)}")


@router.post("/browser/test/{user_id}")
async def create_test_browser_notification(user_id: str):
    """Create a test browser notification for a user"""
    try:
        browser_service = get_browser_notification_service()
        notification = browser_service.create_test_notification(user_id)
        browser_service.queue_notification(notification)

        return {
            "success": True,
            "message": f"Test browser notification created for user {user_id}",
            "notification_id": notification.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test notification: {str(e)}")


@router.delete("/browser/{notification_id}")
async def mark_notification_sent(notification_id: str):
    """Mark a browser notification as sent/handled"""
    try:
        browser_service = get_browser_notification_service()
        success = browser_service.mark_notification_sent(notification_id)

        if success:
            return {"success": True, "message": f"Notification {notification_id} marked as sent"}
        else:
            return {"success": False, "message": f"Notification {notification_id} not found"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification: {str(e)}")


@router.get("/browser/stats")
async def get_browser_notification_stats():
    """Get browser notification statistics"""
    try:
        browser_service = get_browser_notification_service()
        stats = browser_service.get_notification_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notification stats: {str(e)}")


@router.get("/jira/test-config/{user_id}")
async def test_jira_notification_configuration(user_id: str, db: Session = Depends(get_db)):
    """Test Jira native notification service configuration"""
    try:
        from app.services.jira_notification_service import JiraNotificationService
        from app.services.multi_user_jira_service import MultiUserJiraService

        # Get Jira service for user
        multi_jira_service = MultiUserJiraService(db)
        jira_service = multi_jira_service.get_jira_service(user_id)

        if not jira_service:
            return {
                "success": False,
                "message": f"No valid Jira service found for user {user_id}",
                "service": "Jira Cloud Native API",
                "method": "No Authentication"
            }

        # Test connection
        connected = jira_service.is_connected()
        if not connected:
            return {
                "success": False,
                "message": "Jira service is not connected",
                "service": "Jira Cloud Native API",
                "method": "Connection Failed"
            }
          # Get user info to verify notification capability
        user_info = jira_service.myself()
        if user_info:
            return {
                "success": True,
                "message": f"Jira notification service ready for {user_info.get('displayName', 'Unknown')}",
                "service": "Jira Cloud Native API",
                "method": "Issue Notification API",
                "user_account_id": user_info.get('accountId'),
                "user_email": user_info.get('emailAddress')
            }
        else:
            return {
                "success": False,
                "message": "Could not get user information from Jira",
                "service": "Jira Cloud Native API",
                "method": "User Info Failed"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing Jira notification config: {str(e)}")


@router.post("/jira/send-test/{user_id}")
async def send_test_jira_notification(user_id: str, db: Session = Depends(get_db)):
    """Send a test notification using Jira's native notification API"""
    try:
        from app.services.jira_notification_service import JiraNotificationService
        from app.services.multi_user_jira_service import MultiUserJiraService

        # Get Jira service for user
        multi_jira_service = MultiUserJiraService(db)
        jira_service = multi_jira_service.get_jira_service(user_id)

        if not jira_service:
            raise HTTPException(
                status_code=400,
                detail=f"No valid Jira service found for user {user_id}"
            )

        # Create test notification service
        jira_notification_service = JiraNotificationService()

        # Send test notification
        result = await jira_notification_service.test_notification(user_id, jira_service)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending test Jira notification: {str(e)}")


# Jira Notification endpoints
@router.post("/jira/test/{user_id}")
async def test_jira_notification(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Test Jira notification service for a specific user"""
    try:
        from app.services.multi_user_jira_service import MultiUserJiraService
        from app.services.jira_notification_service import JiraNotificationService

        # Get Jira service for the user
        multi_jira_service = MultiUserJiraService(db)
        jira_service = multi_jira_service.get_jira_service(user_id)

        if not jira_service:
            raise HTTPException(status_code=404, detail=f"No valid Jira token found for user {user_id}")

        # Test the Jira notification service
        jira_notification_service = JiraNotificationService()
        result = await jira_notification_service.test_notification(user_id, jira_service)

        return {
            "user_id": user_id,
            "test_result": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing Jira notification: {str(e)}")


@router.get("/jira/user-info/{user_id}")
async def get_jira_user_info(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get Jira user information for debugging"""
    try:
        from app.services.multi_user_jira_service import MultiUserJiraService

        # Get Jira service for the user
        multi_jira_service = MultiUserJiraService(db)
        jira_service = multi_jira_service.get_jira_service(user_id)

        if not jira_service:
            raise HTTPException(status_code=404, detail=f"No valid Jira token found for user {user_id}")
          # Get user info from Jira
        user_info = jira_service.myself()

        return {
            "user_id": user_id,
            "jira_user_info": user_info,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Jira user info: {str(e)}")
