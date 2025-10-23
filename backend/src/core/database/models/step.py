from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from src.core.database.database import Base


class Step(Base):
    """Step model for recipe tutorial steps."""
    __tablename__ = "steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    recipe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=True, default="")
    content: Mapped[str] = mapped_column(Text, nullable=True, default="")
    box_gallery: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=[])  # List of image URLs

    # Relationship
    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="tutorial_steps")
