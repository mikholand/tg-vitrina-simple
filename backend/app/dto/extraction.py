from pydantic import BaseModel, Field

from app.entities.product import Availability


class ProductExtractionSchema(BaseModel):
    """Strict shape the LLM must return. Missing values are null — never guessed."""

    name: str | None = None
    price: float | None = None
    currency: str | None = Field(default=None, max_length=3)
    description: str | None = None
    sku: str | None = None
    availability: Availability = Availability.UNKNOWN
    category: str | None = None


class ExtractionResult(BaseModel):
    content: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
