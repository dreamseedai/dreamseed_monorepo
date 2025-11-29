"""
Email service for user notifications
Supports console mode (dev) and SMTP mode (production)
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

EMAIL_MODE = os.getenv("EMAIL_MODE", "console")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@dreamseedai.com")


def send_verification_email_safe(email: str, token: Optional[str] = None):
    """
    Send verification email (safe wrapper for background tasks)

    Args:
        email: Recipient email address
        token: Verification token (optional)
    """
    try:
        send_verification_email(email, token)
    except Exception as e:
        logger.exception("Failed to send verification email to %s: %s", email, e)


def send_verification_email(email: str, token: Optional[str] = None):
    """
    Send verification email

    In console mode (dev): Just logs, no actual email sent
    In smtp mode (production): Sends actual email via SMTP

    Args:
        email: Recipient email address
        token: Verification token (optional)
    """
    if EMAIL_MODE == "console":
        logger.info("[DEV] Would send verification email to %s", email)
        if token:
            logger.info("[DEV] Verification token: %s", token)
        print(f"📧 [DEV] Verification email for {email}")
        return

    # Production: actual SMTP sending
    logger.info("[PROD] Sending verification email to %s", email)
    _send_email_smtp(
        to=email,
        subject="Verify your DreamSeed account",
        body=f"Please verify your account by clicking the link: {token or 'N/A'}",
    )


def send_password_reset_email_safe(email: str, token: str):
    """
    Send password reset email (safe wrapper for background tasks)

    Args:
        email: Recipient email address
        token: Password reset token
    """
    try:
        send_password_reset_email(email, token)
    except Exception as e:
        logger.exception("Failed to send password reset email to %s: %s", email, e)


def send_password_reset_email(email: str, token: str):
    """
    Send password reset email

    Args:
        email: Recipient email address
        token: Password reset token
    """
    if EMAIL_MODE == "console":
        logger.info("[DEV] Would send password reset email to %s", email)
        logger.info("[DEV] Reset token: %s", token)
        print(f"🔑 [DEV] Password reset email for {email}")
        return

    # Production: actual SMTP sending
    logger.info("[PROD] Sending password reset email to %s", email)
    _send_email_smtp(
        to=email,
        subject="Reset your DreamSeed password",
        body=f"Reset your password using this token: {token}",
    )


def _send_email_smtp(to: str, subject: str, body: str):
    """
    Internal function to send email via SMTP

    This is where actual SMTP connection and sending happens.
    In production, this might be slow (1-5 seconds) depending on SMTP server.

    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (plain text)
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured, skipping email send")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email sent successfully to %s", to)
    except Exception as e:
        logger.error("SMTP error sending to %s: %s", to, e)
        raise
