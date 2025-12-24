"""initial schema

Revision ID: 20251218_initial_schema
Revises: None
Create Date: 2025-12-18 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20251218_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.execute(
        """
        ALTER TABLE articles
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector(
                'simple',
                coalesce(title, '') || ' ' || coalesce(content, '')
            )
        ) STORED;
        """
    )

    op.execute(
        """
        CREATE INDEX ix_articles_search_vector
        ON articles
        USING GIN (search_vector);
        """
    )

    op.create_table(
        "deleted_articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column(
            "deleted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
    )


def downgrade() -> None:
    op.drop_table("deleted_articles")
    op.drop_table("articles")
    op.drop_table("categories")
    op.drop_table("users")
