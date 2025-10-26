"""
Use case: Login a user.
"""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.models import User
from src.core.security import create_access_token, verify_password
from src.schemas.user import UserRead
from src.settings.env import settings


class LoginUseCase:
    """
    Use case for logging in a user.

    Responsibilities:
    - Validate user credentials
    - Check if user is verified
    - Generate access token
    """

    async def execute(self, db: AsyncSession, email: str, password: str) -> dict:
        """
        Execute the use case.

        Args:
            db: Database session
            email: User's email
            password: User's password

        Returns:
            Dict with access_token and user

        Raises:
            ValueError: If credentials invalid or user not verified
        """
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, str(user.password)):
            raise ValueError("Incorrect email or password")

        if not user.verified:
            raise ValueError("Email not verified. Please verify your email before logging in.")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        return {"access_token": access_token, "user": UserRead.model_validate(user)}
