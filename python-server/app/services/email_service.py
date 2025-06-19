"""Email notification service for sending Jira task reminders."""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email configuration settings"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    use_tls: bool = True


class EmailService:
    """Service for sending email notifications about Jira tasks"""

    def __init__(self):
        self.config = self._load_email_config()
        self.enabled = self.config is not None

        if self.enabled:
            logger.info("Email service initialized successfully")
        else:
            logger.warning("Email service disabled - no configuration found")

    def _load_email_config(self) -> Optional[EmailConfig]:
        """Load email configuration from environment variables"""
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = os.getenv('SMTP_PORT', '587')
            username = os.getenv('SMTP_USERNAME')
            password = os.getenv('SMTP_PASSWORD')
            from_email = os.getenv('SMTP_FROM_EMAIL')

            # Check if all required environment variables are present
            if not all([smtp_server, username, password, from_email]):
                logger.info("Email configuration incomplete - some required environment variables missing")
                return None

            return EmailConfig(
                smtp_server=smtp_server,
                smtp_port=int(smtp_port),
                username=username,
                password=password,
                from_email=from_email,
                use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
            )
        except Exception as e:
            logger.error(f"Error loading email configuration: {str(e)}")
            return None

    async def send_due_date_reminder(self, user_email: str, issue_data: Dict[str, Any],
                                   notification_type: str = 'due_soon') -> bool:
        """Send a due date reminder email"""
        if not self.enabled:
            logger.debug("Email service disabled, skipping email notification")
            return False

        if not self.config:
            logger.error("Email configuration not available")
            return False

        try:
            subject = self._generate_subject(issue_data, notification_type)
            body = self._generate_email_body(issue_data, notification_type)

            return await self._send_email(user_email, subject, body)

        except Exception as e:
            logger.error(f"Error sending due date reminder email: {str(e)}")
            return False

    def _generate_subject(self, issue_data: Dict[str, Any], notification_type: str) -> str:
        """Generate email subject line"""
        issue_key = issue_data.get('key', 'Unknown')
        summary = issue_data.get('fields', {}).get('summary', 'No summary')

        if notification_type == 'overdue':
            return f"🚨 OVERDUE: {issue_key} - {summary}"
        elif notification_type == 'due_soon':
            return f"⏰ Due Soon: {issue_key} - {summary}"
        else:
            return f"📋 Jira Reminder: {issue_key} - {summary}"

    def _generate_email_body(self, issue_data: Dict[str, Any], notification_type: str) -> str:
        """Generate email body content"""
        fields = issue_data.get('fields', {})
        issue_key = issue_data.get('key', 'Unknown')
        summary = fields.get('summary', 'No summary')
        due_date = fields.get('duedate', 'No due date')
        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned')
        status = fields.get('status', {}).get('name', 'Unknown')
        priority = fields.get('priority', {}).get('name', 'Medium')

        # Get Jira URL from environment
        jira_url = os.getenv('JIRA_URL', 'https://your-domain.atlassian.net')
        issue_url = f"{jira_url}/browse/{issue_key}"

        # Create HTML email body
        if notification_type == 'overdue':
            status_message = "⚠️  This issue is now OVERDUE and requires immediate attention."
            urgency_color = "#FF5630"
        elif notification_type == 'due_soon':
            status_message = "🔔 This issue is due within the next 24 hours."
            urgency_color = "#FF8B00"
        else:
            status_message = "📋 This is a reminder about your assigned issue."
            urgency_color = "#0052CC"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {urgency_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
                .issue-details {{ background-color: white; padding: 15px; border-radius: 6px; margin: 15px 0; }}
                .button {{ display: inline-block; background-color: #0052CC; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; margin: 10px 0; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Jira Task Reminder</h2>
                    <p>{status_message}</p>
                </div>

                <div class="content">
                    <div class="issue-details">
                        <h3>{issue_key}: {summary}</h3>

                        <p><strong>📅 Due Date:</strong> {due_date}</p>
                        <p><strong>👤 Assignee:</strong> {assignee}</p>
                        <p><strong>📊 Status:</strong> {status}</p>
                        <p><strong>⚡ Priority:</strong> {priority}</p>
                    </div>

                    <a href="{issue_url}" class="button">View Issue in Jira</a>

                    <div style="margin-top: 20px;">
                        <h4>Quick Actions:</h4>
                        <ul>
                            <li>Click the link above to open the issue in Jira</li>
                            <li>Update the status if work is complete</li>
                            <li>Add comments about your progress</li>
                            <li>Adjust the due date if needed</li>
                        </ul>
                    </div>
                </div>

                <div class="footer">
                    <p>This notification was sent by the Jira Chatbot Extension.</p>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_body

    async def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email using SMTP"""
        if not self.config:
            logger.error("Email configuration not available")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.from_email
            msg['To'] = to_email

            # Add HTML content
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()

                server.login(self.config.username, self.config.password)
                server.send_message(msg)

            logger.info(f"Email notification sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def test_email_config(self) -> Dict[str, Any]:
        """Test email configuration and connectivity"""
        if not self.enabled:
            return {
                "success": False,
                "message": "Email service is not configured",
                "config_status": "missing"
            }

        try:
            # Test SMTP connection
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.username, self.config.password)

            return {
                "success": True,
                "message": "Email configuration is working correctly",
                "smtp_server": self.config.smtp_server,
                "smtp_port": self.config.smtp_port,
                "from_email": self.config.from_email
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Email configuration test failed: {str(e)}",
                "error": str(e)
            }
