import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy.sql.functions import func
from sqlalchemy import String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY, BOOLEAN
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base


class Role(PyEnum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model representing a user in the system."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, unique=False, nullable=False, default=False)
    password: Mapped[str] = mapped_column(String, nullable=False)  # Hashed password
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)
    preferences: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=[])  # e.g., ["vegetarian", "gluten-free"]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    pantry: Mapped[list["Pantry"]] = relationship("Pantry", back_populates="user")
    histories: Mapped[list["History"]] = relationship("History", back_populates="user")
