import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import logging

from src.core.template import render_email
from src.settings.env import settings

logger = logging.getLogger(__name__)


def send_email(
    to: str | List[str],
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> bool:
    """
    Send an email using the configured SMTP settings.

    Args:
        to: Recipient email address(es)
        subject: Email subject
        html_content: HTML content of the email
        text_content: Optional plain text content

    Returns:
        True if email was sent successfully, False otherwise
    """
    # Validate SMTP configuration
    if not settings.validate_smtp_config():
        missing_configs = []
        if not settings.SMTP_HOST:
            missing_configs.append("SMTP_HOST")
        if not settings.SMTP_PORT:
            missing_configs.append("SMTP_PORT")
        if not settings.SMTP_USER:
            missing_configs.append("SMTP_USER")
        if not settings.SMTP_PASSWORD:
            missing_configs.append("SMTP_PASSWORD")
        if not settings.EMAILS_FROM_EMAIL:
            missing_configs.append("EMAILS_FROM_EMAIL")

        error_msg = f"Email not sent - SMTP not properly configured. Missing: {', '.join(missing_configs)}"
        logger.error(error_msg)
        print(error_msg)
        return False

    # Convert to list if single recipient
    recipients = to if isinstance(to, list) else [to]

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAILS_FROM_NAME or 'App'} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = ", ".join(recipients)

        # Add plain text part
        if text_content:
            part1 = MIMEText(text_content, "plain")
            message.attach(part1)

        # Add HTML part
        part2 = MIMEText(html_content, "html")
        message.attach(part2)

        logger.info(
            f"Attempting to send email to {recipients} via {settings.SMTP_HOST}:{settings.SMTP_PORT} (TLS={settings.SMTP_TLS})"
        )

        # Connect and send email
        if settings.SMTP_PORT == 465:
            # Use SSL for port 465
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=30
            ) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAILS_FROM_EMAIL, recipients, message.as_string())
        else:
            # Use STARTTLS for port 587
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                server.set_debuglevel(0)  # Set to 1 for debug output
                if settings.SMTP_TLS:
                    server.starttls(context=ssl.create_default_context())
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAILS_FROM_EMAIL, recipients, message.as_string())

        success_msg = f"✓ Email sent successfully: '{subject}' to {recipients}"
        logger.info(success_msg)
        print(success_msg)
        return True

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"✗ SMTP Authentication failed for {recipients}: {e.smtp_code} - {e.smtp_error.decode() if e.smtp_error else 'Unknown error'}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return False
    except smtplib.SMTPConnectError as e:
        error_msg = f"✗ Cannot connect to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT}: {e.smtp_code} - {e.smtp_error.decode() if e.smtp_error else 'Unknown error'}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return False
    except smtplib.SMTPServerDisconnected as e:
        error_msg = f"✗ SMTP server disconnected unexpectedly when sending to {recipients}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return False
    except smtplib.SMTPException as e:
        error_msg = f"✗ SMTP error sending email to {recipients}: {type(e).__name__} - {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return False
    except ConnectionRefusedError as e:
        error_msg = f"✗ Connection refused when sending email to {recipients}: Cannot connect to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT}. Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return False
    except TimeoutError as e:
        error_msg = f"✗ Timeout error sending email to {recipients}: SMTP server did not respond in time. Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return False
    except Exception as e:
        error_msg = f"✗ Unexpected error sending email to {recipients}: {type(e).__name__} - {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return False


def send_verification_email(
    to: str,
    verification_token: str,
    user_name: str | None = None,
    user_email: str | None = None,
    expiry_hours: int = 24,
    company_name: str | None = None,
    logo_url: str | None = None,
    custom_message: str | None = None,
) -> bool:
    """
    Send a verification email to a user.

    Args:
        to: User's email address
        verification_token: Token for email verification
        user_name: User's display name (optional)
        user_email: User's email for display (optional)
        expiry_hours: Hours until verification link expires (default: 24)
        company_name: Company/App name (optional)
        logo_url: Company logo URL (optional)
        custom_message: Additional custom message (optional)

    Returns:
        True if sent successfully
    """
    subject = f"Verify your email - {company_name}" if company_name else "Verify your email"
    context = {
        "verification_url": f"{settings.FRONTEND_URL}/verify?token={verification_token}",
        "frontend_url": settings.FRONTEND_URL,
        "support_email": settings.EMAILS_FROM_EMAIL,
        "user_name": user_name or "there",
        "user_email": user_email or to,
        "expiry_hours": expiry_hours,
        "company_name": company_name or settings.EMAILS_FROM_NAME or "Our Team",
        "logo_url": logo_url,
        "custom_message": custom_message,
    }
    text_content, html_content = render_email("emails/verification", context)
    return send_email(
        to=to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


def send_password_reset_email(
    to: str,
    reset_token: str,
    user_name: str | None = None,
    expiry_hours: int = 1,
    company_name: str | None = None,
) -> bool:
    """
    Send a password reset email to a user.

    Args:
        to: User's email address
        reset_token: Token for password reset
        user_name: User's display name (optional)
        expiry_hours: Hours until reset link expires (default: 1)
        company_name: Company/App name (optional)

    Returns:
        True if sent successfully
    """
    subject = f"Reset your password - {company_name}" if company_name else "Reset your password"
    context = {
        "reset_url": f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
        "frontend_url": settings.FRONTEND_URL,
        "support_email": settings.EMAILS_FROM_EMAIL,
        "user_name": user_name or "there",
        "expiry_hours": expiry_hours,
        "company_name": company_name or settings.EMAILS_FROM_NAME or "Our Team",
    }
    text_content, html_content = render_email("emails/password_reset", context)
    return send_email(
        to=to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )
