from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ArticleBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    category_id: int
    image_url: str | None = Field(default=None, max_length=1024)


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str | None = None
    category_id: int | None = None
    image_url: str | None = Field(default=None, max_length=1024)


class ArticleRead(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseModel):
    items: list[ArticleRead]
    total: int
    page_number: int
    page_size: int
