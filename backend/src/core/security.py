# src/security.py
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.database import get_db
from src.core.database.models.user import User
from src.settings.env import settings

# Password hasher using Argon2
ph = PasswordHasher()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an Argon2 hashed password."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)

# create JWT access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# require verified user
async def get_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return current_user
