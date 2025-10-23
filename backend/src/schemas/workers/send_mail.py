from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


class EmailType(str, Enum):
    """Types of emails that can be sent."""
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"
    CUSTOM = "custom"


class EmailTask(BaseModel):
    """Base schema for email tasks."""
    email_type: EmailType
    to: EmailStr

    class Config:
        use_enum_values = True


class VerificationEmailTask(EmailTask):
    """Schema for verification email task."""
    email_type: EmailType = Field(default=EmailType.VERIFICATION, frozen=True)
    verification_token: str = Field(..., min_length=1)
    user_name: Optional[str] = Field(default=None, description="User's display name")
    user_email: Optional[str] = Field(default=None, description="User's email for display")
    expiry_hours: Optional[int] = Field(default=24, description="Hours until verification link expires")
    company_name: Optional[str] = Field(default=None, description="Company/App name")
    logo_url: Optional[str] = Field(default=None, description="Company logo URL")
    custom_message: Optional[str] = Field(default=None, description="Additional custom message")


class PasswordResetEmailTask(EmailTask):
    """Schema for password reset email task."""
    email_type: EmailType = Field(default=EmailType.PASSWORD_RESET, frozen=True)
    reset_token: str = Field(..., min_length=1)
    user_name: Optional[str] = Field(default=None, description="User's display name")
    expiry_hours: Optional[int] = Field(default=1, description="Hours until reset link expires")
    company_name: Optional[str] = Field(default=None, description="Company/App name")


class CustomEmailTask(EmailTask):
    """Schema for custom email task."""
    email_type: EmailType = Field(default=EmailType.CUSTOM, frozen=True)
    subject: str = Field(..., min_length=1, max_length=200)
    html_content: str = Field(..., min_length=1)
    text_content: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
