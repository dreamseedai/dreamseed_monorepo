"""
Task 4.2: Email Service Module

Multi-channel email notification system with:
- SMTP configuration (Gmail, SendGrid, custom)
- HTML email templates
- Digest emails (daily, weekly)
- Unsubscribe management
- Email preferences
- Bulk sending with rate limiting

Dependencies:
    pip install jinja2 aiosmtplib email-validator
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import asyncio
from pathlib import Path

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.messenger.notifications import NotificationType

logger = logging.getLogger(__name__)

try:
    import aiosmtplib  # type: ignore

    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False
    logger.warning("aiosmtplib not installed. Email sending will be disabled.")


# ============================================================================
# ENUMS
# ============================================================================


class EmailProvider(Enum):
    """Email service providers."""

    SMTP = "smtp"  # Custom SMTP server
    GMAIL = "gmail"  # Gmail SMTP
    SENDGRID = "sendgrid"  # SendGrid API
    SES = "ses"  # Amazon SES


class DigestFrequency(Enum):
    """Digest email frequency."""

    DAILY = "daily"  # Daily digest (sent at 9 AM)
    WEEKLY = "weekly"  # Weekly digest (sent Monday 9 AM)
    REALTIME = "realtime"  # Immediate emails (no digest)
    DISABLED = "disabled"  # No emails


class EmailTemplate(Enum):
    """Email template types."""

    NEW_MESSAGE = "new_message"
    MESSAGE_MENTION = "message_mention"
    CONVERSATION_INVITE = "conversation_invite"
    FILE_UPLOADED = "file_uploaded"
    MODERATION_WARNING = "moderation_warning"
    DIGEST_DAILY = "digest_daily"
    DIGEST_WEEKLY = "digest_weekly"
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"


# ============================================================================
# EMAIL SERVICE
# ============================================================================


class EmailService:
    """
    Multi-channel email notification service.

    Features:
    - SMTP/SendGrid/SES support
    - HTML templates with Jinja2
    - Digest emails (daily/weekly)
    - Unsubscribe management
    - Rate limiting
    - Bulk sending
    """

    def __init__(self):
        """Initialize email service."""
        # SMTP Configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        # SendGrid Configuration
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")

        # Amazon SES Configuration
        self.ses_region = os.getenv("SES_REGION", "us-east-1")
        self.ses_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.ses_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")

        # Email Settings
        self.from_email = os.getenv("EMAIL_FROM", "noreply@dreamseed.ai")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "DreamSeed Messenger")
        self.reply_to = os.getenv("EMAIL_REPLY_TO", "support@dreamseed.ai")

        # Provider Selection
        provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()
        self.provider = EmailProvider(provider)

        # Rate Limiting
        self.rate_limit_per_hour = int(os.getenv("EMAIL_RATE_LIMIT", "100"))
        self.rate_limit_window = 3600  # 1 hour in seconds
        self._rate_limit_counter: Dict[str, List[float]] = {}

        # Template Engine
        template_dir = Path(__file__).parent.parent / "templates" / "emails"
        template_dir.mkdir(parents=True, exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Digest Configuration
        self.digest_daily_hour = int(os.getenv("DIGEST_DAILY_HOUR", "9"))  # 9 AM
        self.digest_weekly_day = 0  # Monday (0=Monday, 6=Sunday)

        logger.info(f"EmailService initialized with provider: {self.provider.value}")

    # ========================================================================
    # SMTP DELIVERY
    # ========================================================================

    async def send_email_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            attachments: List of attachments (optional)

        Returns:
            True if sent successfully
        """
        try:
            # Check rate limit
            if not self._check_rate_limit(to_email):
                logger.warning(f"Rate limit exceeded for {to_email}")
                return False

            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            message["Reply-To"] = self.reply_to

            # Add text part (fallback)
            if text_body:
                text_part = MIMEText(text_body, "plain", "utf-8")
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)

            # Add attachments
            if attachments:
                for attachment in attachments:
                    if attachment.get("type") == "image":
                        img = MIMEImage(attachment["data"])
                        img.add_header("Content-ID", f"<{attachment['cid']}>")
                        message.attach(img)

            # Check if aiosmtplib is available
            if not AIOSMTPLIB_AVAILABLE:
                logger.error("aiosmtplib not installed. Cannot send email.")
                return False

            # Send via SMTP
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.smtp_use_tls,
            ) as smtp:
                if self.smtp_username and self.smtp_password:
                    await smtp.login(self.smtp_username, self.smtp_password)

                await smtp.send_message(message)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_email_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """Send email via SendGrid API."""
        try:
            # Check rate limit
            if not self._check_rate_limit(to_email):
                logger.warning(f"Rate limit exceeded for {to_email}")
                return False

            # TODO: Implement SendGrid API integration
            # from sendgrid import SendGridAPIClient
            # from sendgrid.helpers.mail import Mail

            logger.warning("SendGrid integration not implemented yet")
            return False

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid to {to_email}: {e}")
            return False

    async def send_email_ses(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """Send email via Amazon SES."""
        try:
            # Check rate limit
            if not self._check_rate_limit(to_email):
                logger.warning(f"Rate limit exceeded for {to_email}")
                return False

            # TODO: Implement Amazon SES integration
            # import boto3
            # ses_client = boto3.client('ses', region_name=self.ses_region)

            logger.warning("Amazon SES integration not implemented yet")
            return False

        except Exception as e:
            logger.error(f"Failed to send email via SES to {to_email}: {e}")
            return False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Send email using configured provider.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            attachments: List of attachments (optional)

        Returns:
            True if sent successfully
        """
        if self.provider == EmailProvider.SMTP or self.provider == EmailProvider.GMAIL:
            return await self.send_email_smtp(
                to_email, subject, html_body, text_body, attachments
            )
        elif self.provider == EmailProvider.SENDGRID:
            return await self.send_email_sendgrid(
                to_email, subject, html_body, text_body
            )
        elif self.provider == EmailProvider.SES:
            return await self.send_email_ses(to_email, subject, html_body, text_body)
        else:
            logger.error(f"Unknown email provider: {self.provider}")
            return False

    # ========================================================================
    # TEMPLATE RENDERING
    # ========================================================================

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> tuple[str, str]:
        """
        Render email template.

        Args:
            template_name: Template filename (e.g., "new_message.html")
            context: Template context variables

        Returns:
            Tuple of (html_body, text_body)
        """
        try:
            # Add common context
            context.update(
                {
                    "site_name": "DreamSeed",
                    "site_url": os.getenv("SITE_URL", "https://dreamseed.ai"),
                    "support_email": self.reply_to,
                    "current_year": datetime.now().year,
                }
            )

            # Render HTML template
            html_template = self.jinja_env.get_template(template_name)
            html_body = html_template.render(context)

            # Render text template (fallback)
            text_template_name = template_name.replace(".html", ".txt")
            try:
                text_template = self.jinja_env.get_template(text_template_name)
                text_body = text_template.render(context)
            except Exception:
                # Generate simple text version from context
                text_body = self._generate_text_fallback(context)

            return html_body, text_body

        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def _generate_text_fallback(self, context: Dict[str, Any]) -> str:
        """Generate simple text version from context."""
        lines = [
            f"{context.get('title', 'Notification')}",
            "",
            f"{context.get('message', '')}",
            "",
            f"View in DreamSeed: {context.get('action_url', context.get('site_url', ''))}",
            "",
            f"---",
            f"DreamSeed Messenger",
            f"{context.get('support_email', '')}",
        ]
        return "\n".join(lines)

    # ========================================================================
    # NOTIFICATION EMAILS
    # ========================================================================

    async def send_notification_email(
        self,
        user_email: str,
        notification_type: NotificationType,
        data: Dict[str, Any],
    ) -> bool:
        """
        Send notification email.

        Args:
            user_email: User's email address
            notification_type: Type of notification
            data: Notification data

        Returns:
            True if sent successfully
        """
        try:
            # Map notification type to template
            template_map = {
                NotificationType.NEW_MESSAGE: "new_message.html",
                NotificationType.MESSAGE_MENTION: "message_mention.html",
                NotificationType.CONVERSATION_INVITE: "conversation_invite.html",
                NotificationType.FILE_UPLOADED: "file_uploaded.html",
                NotificationType.MODERATION_WARNING: "moderation_warning.html",
            }

            template_name = template_map.get(notification_type)
            if not template_name:
                logger.warning(f"No email template for {notification_type}")
                return False

            # Prepare context
            context = {
                "title": self._get_notification_title(notification_type, data),
                "message": data.get("message", ""),
                "action_url": data.get("action_url", ""),
                "sender": data.get("sender", "Someone"),
                "conversation": data.get("conversation", "a conversation"),
                "preview": data.get("preview", ""),
                "file_name": data.get("file_name", ""),
                "reason": data.get("reason", ""),
            }

            # Render template
            html_body, text_body = self.render_template(template_name, context)

            # Get subject
            subject = self._get_notification_subject(notification_type, data)

            # Send email
            return await self.send_email(
                to_email=user_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

        except Exception as e:
            logger.error(f"Failed to send notification email: {e}")
            return False

    def _get_notification_title(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any],
    ) -> str:
        """Get notification title."""
        titles = {
            NotificationType.NEW_MESSAGE: f"New message from {data.get('sender', 'Someone')}",
            NotificationType.MESSAGE_MENTION: f"{data.get('sender', 'Someone')} mentioned you",
            NotificationType.CONVERSATION_INVITE: f"Invitation to {data.get('conversation', 'a conversation')}",
            NotificationType.FILE_UPLOADED: f"{data.get('sender', 'Someone')} shared a file",
            NotificationType.MODERATION_WARNING: "⚠️ Moderation Warning",
        }
        return titles.get(notification_type, "Notification")

    def _get_notification_subject(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any],
    ) -> str:
        """Get email subject."""
        subjects = {
            NotificationType.NEW_MESSAGE: f"New message from {data.get('sender', 'Someone')}",
            NotificationType.MESSAGE_MENTION: f"{data.get('sender', 'Someone')} mentioned you",
            NotificationType.CONVERSATION_INVITE: f"You're invited to {data.get('conversation', 'a conversation')}",
            NotificationType.FILE_UPLOADED: f"New file: {data.get('file_name', 'File')}",
            NotificationType.MODERATION_WARNING: "⚠️ Important: Moderation Warning",
        }
        return subjects.get(notification_type, "DreamSeed Notification")

    # ========================================================================
    # DIGEST EMAILS
    # ========================================================================

    async def send_digest_email(
        self,
        db: AsyncSession,
        user_id: int,
        frequency: DigestFrequency,
    ) -> bool:
        """
        Send digest email.

        Args:
            db: Database session
            user_id: User ID
            frequency: Digest frequency (daily/weekly)

        Returns:
            True if sent successfully
        """
        try:
            # Get user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                return False

            # Get email value
            user_email = getattr(user, "email", None)
            if not user_email or not isinstance(user_email, str):
                return False

            # Get notifications for period
            if frequency == DigestFrequency.DAILY:
                since = datetime.utcnow() - timedelta(days=1)
                template_name = "digest_daily.html"
                subject = "Daily Digest - DreamSeed Messenger"
            elif frequency == DigestFrequency.WEEKLY:
                since = datetime.utcnow() - timedelta(days=7)
                template_name = "digest_weekly.html"
                subject = "Weekly Digest - DreamSeed Messenger"
            else:
                logger.warning(f"Invalid digest frequency: {frequency}")
                return False

            # Get unread notifications from in_app_notifications table
            from app.models import InAppNotification

            result = await db.execute(
                select(InAppNotification)
                .where(
                    and_(
                        InAppNotification.user_id == user_id,
                        InAppNotification.created_at >= since,
                        InAppNotification.is_read == False,
                    )
                )
                .order_by(InAppNotification.created_at.desc())
                .limit(50)
            )
            notifications = result.scalars().all()

            if not notifications:
                logger.info(f"No notifications for digest: user_id={user_id}")
                return False

            # Group notifications by type
            grouped_notifications = self._group_notifications(list(notifications))

            # Prepare context
            context = {
                "user_name": user.full_name or str(user.email),
                "period": (
                    "yesterday" if frequency == DigestFrequency.DAILY else "this week"
                ),
                "total_notifications": len(notifications),
                "grouped_notifications": grouped_notifications,
                "unsubscribe_url": f"{os.getenv('SITE_URL', '')}/settings/notifications?unsubscribe=digest",
            }

            # Render template
            html_body, text_body = self.render_template(template_name, context)

            # Send email
            return await self.send_email(
                to_email=user_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

        except Exception as e:
            logger.error(f"Failed to send digest email: {e}")
            return False

    def _group_notifications(
        self,
        notifications: List[Any],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group notifications by type."""
        grouped = {}

        for notification in notifications:
            notification_type = notification.type

            if notification_type not in grouped:
                grouped[notification_type] = []

            grouped[notification_type].append(
                {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data or {},
                    "action_url": notification.action_url,
                    "created_at": notification.created_at,
                }
            )

        return grouped

    async def send_digest_emails_batch(
        self,
        db: AsyncSession,
        frequency: DigestFrequency,
    ) -> int:
        """
        Send digest emails to all users who have enabled it.

        Args:
            db: Database session
            frequency: Digest frequency

        Returns:
            Number of emails sent
        """
        try:
            # Get users with digest enabled
            from app.models import NotificationPreference

            result = await db.execute(
                select(User)
                .join(
                    NotificationPreference,
                    NotificationPreference.user_id == User.id,
                )
                .where(
                    and_(
                        NotificationPreference.channel == "email",
                        NotificationPreference.enabled == True,
                    )
                )
                .distinct()
            )
            users = result.scalars().all()

            # Send digest to each user
            count = 0
            for user in users:
                user_id = getattr(user, "id", None)
                if user_id is None:
                    continue
                success = await self.send_digest_email(db, user_id, frequency)
                if success:
                    count += 1

                # Rate limiting delay
                await asyncio.sleep(0.1)

            logger.info(f"Sent {count} {frequency.value} digest emails")
            return count

        except Exception as e:
            logger.error(f"Failed to send digest emails batch: {e}")
            return 0

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    def _check_rate_limit(self, email: str) -> bool:
        """
        Check if email is within rate limit.

        Args:
            email: Email address

        Returns:
            True if within rate limit
        """
        now = datetime.utcnow().timestamp()

        # Initialize counter for email
        if email not in self._rate_limit_counter:
            self._rate_limit_counter[email] = []

        # Remove old timestamps
        self._rate_limit_counter[email] = [
            ts
            for ts in self._rate_limit_counter[email]
            if now - ts < self.rate_limit_window
        ]

        # Check limit
        if len(self._rate_limit_counter[email]) >= self.rate_limit_per_hour:
            return False

        # Add current timestamp
        self._rate_limit_counter[email].append(now)
        return True

    # ========================================================================
    # BULK SENDING
    # ========================================================================

    async def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        template_name: str,
        subject: str,
    ) -> int:
        """
        Send bulk emails.

        Args:
            recipients: List of {"email": str, "context": dict}
            template_name: Template filename
            subject: Email subject

        Returns:
            Number of emails sent successfully
        """
        count = 0

        for recipient in recipients:
            try:
                # Render template
                html_body, text_body = self.render_template(
                    template_name,
                    recipient["context"],
                )

                # Send email
                success = await self.send_email(
                    to_email=recipient["email"],
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                )

                if success:
                    count += 1

                # Rate limiting delay
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(
                    f"Failed to send bulk email to {recipient.get('email')}: {e}"
                )

        logger.info(f"Sent {count}/{len(recipients)} bulk emails")
        return count


# ============================================================================
# SINGLETON
# ============================================================================

_email_service_instance: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get singleton email service instance."""
    global _email_service_instance

    if _email_service_instance is None:
        _email_service_instance = EmailService()

    return _email_service_instance
