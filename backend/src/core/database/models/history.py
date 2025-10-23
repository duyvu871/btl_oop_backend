from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from src.core.database.database import Base

class History(Base):
    """History model for user's recipe interactions."""
    __tablename__ = "histories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="histories")
    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="histories")
