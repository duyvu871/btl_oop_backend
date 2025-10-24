from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be between 8 and 128 characters"
    )

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Validate password length. Argon2 supports much longer passwords than bcrypt."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password cannot be longer than 128 characters')
        return v


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_name: str
    email: str
    verified: bool
    role: str
    preferences: list[str]
    created_at: datetime


class UserAdminRead(BaseModel):
    """Extended user information for admin view"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_name: str
    email: str
    verified: bool
    role: str
    preferences: list[str]
    created_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating user information by admin"""
    user_name: str | None = None
    email: EmailStr | None = None
    verified: bool | None = None
    role: str | None = None
    preferences: list[str] | None = None


class UserListResponse(BaseModel):
    """Paginated user list response"""
    total: int
    page: int
    page_size: int
    users: list[UserAdminRead]


class UserAdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be between 8 and 128 characters"
    )
    user_name: str | None = None
    role: str = "user"
    verified: bool = False
    preferences: list[str] = []

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Validate password length. Argon2 supports much longer passwords than bcrypt."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password cannot be longer than 128 characters')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ["user", "admin"]:
            raise ValueError('Role must be "user" or "admin"')
        return v
