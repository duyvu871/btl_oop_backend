from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base

if TYPE_CHECKING:
    from .ingredient import Ingredient
    from .user import User


class Pantry(Base):
    """Pantry model for user's personal ingredients."""

    __tablename__ = "pantries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False)
    quantity: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "2 quả", "500g"
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # Expiration date

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="pantry")  # noqa: F821
    ingredient: Mapped[Ingredient] = relationship("Ingredient", back_populates="pantries")  # noqa: F821
