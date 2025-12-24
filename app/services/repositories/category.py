from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.category import Category
from app.schemas.category import CategoryCreate


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CategoryCreate) -> Category:
        logger.info(
            "CategoryRepository.create: name={name} slug={slug}",
            name=data.name,
            slug=data.slug,
        )
        category = Category(
            name=data.name,
            slug=data.slug,
            description=data.description,
        )
        self._session.add(category)
        await self._session.commit()
        await self._session.refresh(category)
        logger.info(
            "CategoryRepository.create: created id={id} name={name} slug={slug}",
            id=category.id,
            name=category.name,
            slug=category.slug,
        )
        return category

    async def list_all(self) -> Sequence[Category]:
        logger.debug("CategoryRepository.list_all called")
        stmt = select(Category).order_by(Category.name)
        result = await self._session.execute(stmt)
        categories = result.scalars().all()
        logger.debug(
            "CategoryRepository.list_all: count={count}", count=len(categories)
        )
        return categories
