from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Standard message response shared across all routes."""
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response."""
    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
