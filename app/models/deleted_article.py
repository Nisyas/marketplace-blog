from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DeletedArticle(Base):
    __tablename__ = "deleted_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    category_id: Mapped[int] = mapped_column(Integer, nullable=False)

    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
