from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CategoryCreate) -> Category:
        category = Category(
            name=data.name,
            slug=data.slug,
            description=data.description,
        )
        self._session.add(category)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(category)
        return category

    async def list_all(self) -> Sequence[Category]:
        stmt = select(Category).order_by(Category.name)
        result = await self._session.execute(stmt)
        return result.scalars().all()
