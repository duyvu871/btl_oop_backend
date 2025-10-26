"""
Helper class for auth use cases.
Provides convenient wrappers around use cases.
"""


from .login_by_username import LoginByUsernameUseCase
from .login_user import LoginUseCase
from .register_user import RegisterUserUseCase


class AuthUseCase:
    """
    Helper class that wraps auth use cases.
    Designed to be used with FastAPI dependency injection.

    Example:
        @app.post("/auth/register")
        async def register(
            helper: AuthUseCase = Depends(get_auth_usecase)
        ):
            user = await helper.register(db, user_in)
    """

    def __init__(self):
        pass

    async def register(self, db, user_in):
        """
        Register a new user.

        Args:
            db: Database session
            user_in: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user already exists
        """
        use_case = RegisterUserUseCase()
        return await use_case.execute(db, user_in)

    async def login(self, db, email, password):
        """
        Login a user.

        Args:
            db: Database session
            email: User's email
            password: User's password

        Returns:
            Dict with access_token and user

        Raises:
            ValueError: If credentials invalid or not verified
        """
        use_case = LoginUseCase()
        return await use_case.execute(db, email, password)

    async def login_by_username(self, db, username, password):
        """
        Login a user by username.

        Args:
            db: Database session
            username: User's username
            password: User's password

        Returns:
            Dict with access_token and token_type

        Raises:
            ValueError: If credentials invalid
        """
        use_case = LoginByUsernameUseCase()
        return await use_case.execute(db, username, password)


def get_auth_usecase() -> AuthUseCase:
    """
    Dependency injection for AuthUseCase.
    """
    return AuthUseCase()
