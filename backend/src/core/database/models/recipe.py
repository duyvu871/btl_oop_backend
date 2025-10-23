from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base

if TYPE_CHECKING:
    from .history import History
    from .ingredient import Ingredient
    from .step import Step


class Recipe(Base):
    """Recipe model representing a recipe in the system."""
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    thumbnail: Mapped[str] = mapped_column(String, nullable=True)  # Optional image
    tutorial: Mapped[str] = mapped_column(Text, nullable=False)
    quantitative: Mapped[str] = mapped_column(Text, nullable=False)
    ingredientTitle: Mapped[str] = mapped_column(Text, nullable=False)  # noqa: N815
    ingredientMarkdown: Mapped[str] = mapped_column(Text, nullable=False)  # noqa: N815
    stepMarkdown: Mapped[str] = mapped_column(Text, nullable=False)  # noqa: N815
    embedded_ingredient: Mapped[list[float]] = mapped_column(ARRAY(Float, dimensions=1), nullable=True, default=[])  # vector(3072)
    embedded_name: Mapped[list[float]] = mapped_column(ARRAY(Float, dimensions=1), nullable=True, default=[])        # vector(3072)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tutorial_steps: Mapped[list[Step]] = relationship("Step", back_populates="recipe")  # noqa: F821
    ingredients: Mapped[list[Ingredient]] = relationship("Ingredient", back_populates="recipe")  # noqa: F821
    histories: Mapped[list[History]] = relationship("History", back_populates="recipe")  # noqa: F821
