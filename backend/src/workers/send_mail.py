"""
ARQ Worker for sending emails asynchronously via Redis queue.
"""
import logging
from typing import Any, Dict

from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from redis.asyncio import Redis

from src.settings.env import settings
from src.core.services.email import (
    send_email,
    send_verification_email,
    send_password_reset_email,
)
from src.schemas.workers.send_mail import (
    EmailType,
    VerificationEmailTask,
    PasswordResetEmailTask,
    CustomEmailTask,
)

logger = logging.getLogger(__name__)


async def send_email_task(ctx: Dict[str, Any], email_data: Dict[str, Any]) -> bool:
    """
    ARQ task to send emails based on email type.

    Args:
        ctx: ARQ context (contains redis pool and other info)
        email_data: Dictionary containing email task data

    Returns:
        True if email sent successfully, False otherwise
    """
    email_type = email_data.get("email_type")
    recipient = email_data.get("to", "unknown")

    try:
        if email_type == EmailType.VERIFICATION.value:
            # Validate with Pydantic schema
            try:
                task = VerificationEmailTask(**email_data)
            except Exception as validation_error:
                logger.error(f"Validation error for verification email task: {validation_error}", exc_info=True)
                raise

            logger.info(f"Sending verification email to {task.to}")
            result = send_verification_email(
                to=task.to,
                verification_token=task.verification_token,
                user_name=task.user_name,
                user_email=task.user_email,
                expiry_hours=task.expiry_hours,
                company_name=task.company_name,
                logo_url=task.logo_url,
                custom_message=task.custom_message,
            )

        elif email_type == EmailType.PASSWORD_RESET.value:
            # Validate with Pydantic schema
            try:
                task = PasswordResetEmailTask(**email_data)
            except Exception as validation_error:
                logger.error(f"Validation error for password reset email task: {validation_error}", exc_info=True)
                raise

            logger.info(f"Sending password reset email to {task.to}")
            result = send_password_reset_email(
                to=task.to,
                reset_token=task.reset_token,
                user_name=task.user_name,
                expiry_hours=task.expiry_hours,
                company_name=task.company_name,
            )

        elif email_type == EmailType.CUSTOM.value:
            # Validate with Pydantic schema
            try:
                task = CustomEmailTask(**email_data)
            except Exception as validation_error:
                logger.error(f"Validation error for custom email task: {validation_error}", exc_info=True)
                raise

            logger.info(f"Sending custom email to {task.to}: {task.subject}")
            result = send_email(
                to=task.to,
                subject=task.subject,
                html_content=task.html_content,
                text_content=task.text_content,
            )

        else:
            error_msg = f"Unknown email type: {email_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if result:
            logger.info(f"✓ Email sent successfully: {email_type} to {recipient}")
        else:
            logger.error(f"✗ Failed to send email: {email_type} to {recipient} (check email service logs for details)")

        return result

    except ValueError as e:
        logger.error(f"Value error in send_email_task for {email_type} to {recipient}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in send_email_task for {email_type} to {recipient}: "
            f"{type(e).__name__} - {str(e)}",
            exc_info=True
        )
        raise


async def startup(ctx: Dict[str, Any]) -> None:
    """
    Worker startup function - runs when worker starts.
    Initialize connections here if needed.
    """
    logger.info("ARQ Email worker starting up...")
    ctx["startup_complete"] = True


async def shutdown(ctx: Dict[str, Any]) -> None:
    """
    Worker shutdown function - runs when worker stops.
    Clean up connections here if needed.
    """
    logger.info("ARQ Email worker shutting down...")


class WorkerSettings:
    """
    ARQ Worker settings configuration.
    """
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DB,
    )

    # Task functions available to the worker
    functions = [send_email_task]

    # Worker configuration
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = settings.ARQ_MAX_JOBS
    job_timeout = settings.ARQ_JOB_TIMEOUT
    queue_name = settings.ARQ_QUEUE_NAME

    # Retry configuration
    max_tries = 3
    retry_delay = 60  # Retry after 60 seconds


async def get_redis_pool() -> ArqRedis:
    """
    Get ARQ Redis pool for enqueueing jobs.

    Returns:
        ArqRedis pool instance
    """
    return await create_pool(
        RedisSettings(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            database=settings.REDIS_DB,
        )
    )


async def enqueue_email(email_data: Dict[str, Any]) -> str | None:
    """
    Enqueue an email task to be processed by the worker.

    Args:
        email_data: Dictionary containing email task data

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    try:
        redis = await get_redis_pool()
        job = await redis.enqueue_job(
            "send_email_task",
            email_data
        )
        logger.info(f"Email job enqueued: {job.job_id}")
        await redis.close()
        return job.job_id
    except Exception as e:
        logger.error(f"Failed to enqueue email job: {e}", exc_info=True)
        return None
