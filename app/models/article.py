from datetime import datetime

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        nullable=False,
    )

    category: Mapped["Category"] = relationship(back_populates="articles")  # noqa: F821

    __table_args__ = (
        Index(
            "ix_articles_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )
