from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base

if TYPE_CHECKING:
    from .pantry import Pantry
    from .recipe import Recipe


class Ingredient(Base):
    """Ingredient model for recipe ingredients."""
    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    recipe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "3 quả"
    unit: Mapped[str] = mapped_column(String, nullable=False)  # Measurement unit

    # Relationships
    recipe: Mapped[Recipe] = relationship("Recipe", back_populates="ingredients")  # noqa: F821
    pantries: Mapped[list[Pantry]] = relationship("Pantry", back_populates="ingredient")  # noqa: F821
