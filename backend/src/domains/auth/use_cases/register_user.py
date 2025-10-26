"""
Use case: Register a new user.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.models import User
from src.core.security import get_password_hash
from src.schemas.user import UserCreate


class RegisterUserUseCase:
    """
    Use case for registering a new user.

    Responsibilities:
    - Validate user doesn't exist
    - Hash password
    - Create and save user to database
    """

    async def execute(self, db: AsyncSession, user_in: UserCreate) -> User:
        """
        Execute the use case.

        Args:
            db: Database session
            user_in: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user already exists
        """
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_in.email))
        user = result.scalar_one_or_none()

        if user:
            raise ValueError("Email already registered")

        user_name = str(user_in.email).split("@")[0]
        hashed_password = get_password_hash(user_in.password)
        new_user = User(user_name=user_name, email=str(user_in.email), password=hashed_password)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user
