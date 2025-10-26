from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IngredientRead(BaseModel):
    """Schema for ingredient in recipe response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    quantity: str | None = None
    unit: str | None = None


class TutorialStepRead(BaseModel):
    """Schema for tutorial step in recipe response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    index: int
    title: str | None = None
    content: str
    box_gallery: list[str] = None


class RecipeRead(BaseModel):
    """Schema for recipe response with full details"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    link: str | None = None
    title: str
    thumbnail: str | None = None
    tutorial: str | None = None
    quantitative: str | None = None
    # ingredientTitle: str | None = None
    # ingredientMarkdown: str | None = None
    # stepMarkdown: str | None = None
    # created_at: datetime | None = None
    # updated_at: datetime | None = None
    ingredients: list[IngredientRead] = Field(default_factory=list)
    tutorial_steps: list[TutorialStepRead] = Field(default_factory=list)


class RecommendRequest(BaseModel):
    """Schema for recommendation request"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Text describing what you want to cook or ingredients you have",
        examples=["I want to make pasta with tomatoes", "chicken and rice"],
    )


class RecommendResponse(BaseModel):
    """Schema for recommendation response"""

    message: str
    recipes: list[RecipeRead]
    total: int = Field(description="Total number of recipes returned")


class SearchResponse(BaseModel):
    """Schema for search response"""

    recipes: list[RecipeRead]
    total: int = Field(description="Total number of recipes matching the query")
    page: int | None = Field(default=None, description="Current page number")
    size: int | None = Field(default=None, description="Number of recipes per page")
