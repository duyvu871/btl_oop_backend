from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, Field, ConfigDict
from typing import List
from uuid import UUID


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
    email: str
    role: str
    preferences: List[str]
    created_at: datetime
