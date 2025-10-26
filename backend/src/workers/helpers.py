"""
Helper utilities for working with ARQ email worker.
"""

import logging
from typing import Any

from src.schemas.workers.send_mail import (
    CustomEmailTask,
    EmailType,
    PasswordResetEmailTask,
    VerificationEmailTask,
)
from src.workers.send_mail import enqueue_email

logger = logging.getLogger(__name__)


async def queue_verification_email(
    email: str,
    verification_token: str,
    user_name: str | None = None,
    user_email: str | None = None,
    expiry_hours: int = 24,
    company_name: str | None = None,
    logo_url: str | None = None,
    custom_message: str | None = None,
) -> str | None:
    """
    Queue a use_cases email to be sent.

    Args:
        email: Recipient email address
        verification_token: Verification token
        user_name: User's display name (optional)
        user_email: User's email for display (optional)
        expiry_hours: Hours until use_cases link expires (default: 24)
        company_name: Company/App name (optional)
        logo_url: Company logo URL (optional)
        custom_message: Additional custom message (optional)

    Returns:
        Job ID if queued successfully, None otherwise
    """
    task = VerificationEmailTask(
        email_type=EmailType.VERIFICATION,
        to=email,
        verification_token=verification_token,
        user_name=user_name,
        user_email=user_email,
        expiry_hours=expiry_hours,
        company_name=company_name,
        logo_url=logo_url,
        custom_message=custom_message,
    )
    return await enqueue_email(task.model_dump())


async def queue_password_reset_email(
    email: str,
    reset_token: str,
    user_name: str | None = None,
    expiry_hours: int = 1,
    company_name: str | None = None,
) -> str | None:
    """
    Queue a password reset email to be sent.

    Args:
        email: Recipient email address
        reset_token: Password reset token
        user_name: User's display name (optional)
        expiry_hours: Hours until reset link expires (default: 1)
        company_name: Company/App name (optional)

    Returns:
        Job ID if queued successfully, None otherwise
    """
    task = PasswordResetEmailTask(
        email_type=EmailType.PASSWORD_RESET,
        to=email,
        reset_token=reset_token,
        user_name=user_name,
        expiry_hours=expiry_hours,
        company_name=company_name,
    )
    return await enqueue_email(task.model_dump())


async def queue_custom_email(
    email: str, subject: str, html_content: str, text_content: str | None = None, context: dict[str, Any] | None = None
) -> str | None:
    """
    Queue a custom email to be sent.

    Args:
        email: Recipient email address
        subject: Email subject
        html_content: HTML content
        text_content: Plain text content (optional)
        context: Additional context data (optional)

    Returns:
        Job ID if queued successfully, None otherwise
    """
    task = CustomEmailTask(
        email_type=EmailType.CUSTOM,
        to=email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        context=context,
    )
    return await enqueue_email(task.model_dump())
