"""
Verification use cases.

This package contains all use cases related to verification workflows:
- Email verification
- Password reset
- 2FA (future)
"""
from .generate_email_verification import GenerateEmailVerificationUseCase
from .verify_email_code import VerifyEmailCodeUseCase
from .generate_password_reset import GeneratePasswordResetUseCase
from .verify_password_reset_code import VerifyPasswordResetCodeUseCase
from .helpers import (
    VerificationUseCase,
    get_verification_usecase,
)

__all__ = [
    # Use cases
    "GenerateEmailVerificationUseCase",
    "VerifyEmailCodeUseCase",
    "GeneratePasswordResetUseCase",
    "VerifyPasswordResetCodeUseCase",
    # Helpers
    "VerificationUseCase",
    "get_verification_usecase",
]
