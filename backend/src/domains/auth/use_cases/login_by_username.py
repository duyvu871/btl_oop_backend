"""
Use case: Login a user by username.
"""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.models import User
from src.core.security import create_access_token, verify_password
from src.settings.env import settings


class LoginByUsernameUseCase:
    """
    Use case for logging in a user by username.

    Responsibilities:
    - Validate user credentials by username
    - Generate access token
    """

    async def execute(self, db: AsyncSession, username: str, password: str) -> dict:
        """
        Execute the use case.

        Args:
            db: Database session
            username: User's username
            password: User's password

        Returns:
            Dict with access_token and token_type

        Raises:
            ValueError: If credentials invalid
        """
        result = await db.execute(select(User).where(User.user_name == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, str(user.password)):
            raise ValueError("Invalid credentials")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
