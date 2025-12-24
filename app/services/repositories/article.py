from datetime import datetime, timezone

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_
from loguru import logger

from app.models.article import Article
from app.models.deleted_article import DeletedArticle
from app.schemas.article import ArticleCreate, ArticleUpdate


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self) -> Select:
        return select(Article).where(Article.is_deleted.is_(False))

    async def list_articles(
        self,
        *,
        search: str | None,
        category_id: int | None,
        page_number: int,
        page_size: int,
    ) -> tuple[list[Article], int]:
        logger.debug(
            "ArticleRepository.list_articles: search={search} category_id={category_id} page_number={page_number} page_size={page_size}",
            search=search,
            category_id=category_id,
            page_number=page_number,
            page_size=page_size,
        )

        query = self._base_query()

        conditions = []
        if search:
            ts_query = func.plainto_tsquery("simple", search)
            conditions.append(Article.search_vector.op("@@")(ts_query))

        if category_id is not None:
            conditions.append(Article.category_id == category_id)

        if conditions:
            query = query.where(and_(*conditions))

        count_stmt = select(func.count()).select_from(query.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page_number - 1) * page_size
        query = (
            query.order_by(Article.created_at.desc()).offset(offset).limit(page_size)
        )

        result = await self._session.execute(query)
        items = result.scalars().all()

        logger.debug(
            "ArticleRepository.list_articles: total={total} returned={returned}",
            total=total,
            returned=len(items),
        )

        return items, total

    async def get_by_id(self, article_id: int) -> Article | None:
        logger.debug("ArticleRepository.get_by_id: id={id}", id=article_id)
        stmt = self._base_query().where(Article.id == article_id)
        result = await self._session.execute(stmt)
        article = result.scalar_one_or_none()
        if article is None:
            logger.debug(
                "ArticleRepository.get_by_id: not found id={id}", id=article_id
            )
        else:
            logger.debug(
                "ArticleRepository.get_by_id: found id={id} title={title}",
                id=article.id,
                title=article.title,
            )
        return article

    async def create(self, data: ArticleCreate) -> Article:
        logger.info(
            "ArticleRepository.create: title={title} category_id={category_id} has_image={has_image}",
            title=data.title,
            category_id=data.category_id,
            has_image=data.image_url is not None,
        )
        article = Article(
            title=data.title,
            content=data.content,
            category_id=data.category_id,
            image_url=data.image_url,
        )
        self._session.add(article)
        await self._session.commit()
        await self._session.refresh(article)
        logger.info(
            "ArticleRepository.create: created id={id} title={title} category_id={category_id}",
            id=article.id,
            title=article.title,
            category_id=article.category_id,
        )
        return article

    async def update(self, article: Article, data: ArticleUpdate) -> Article:
        logger.info("ArticleRepository.update: id={id}", id=article.id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(article, field, value)
        await self._session.commit()
        await self._session.refresh(article)
        logger.info(
            "ArticleRepository.update: updated id={id} title={title}",
            id=article.id,
            title=article.title,
        )
        return article

    async def soft_delete(self, article: Article) -> None:
        logger.info(
            "ArticleRepository.soft_delete: id={id} title={title}",
            id=article.id,
            title=article.title,
        )

        deleted = DeletedArticle(
            original_id=article.id,
            title=article.title,
            content=article.content,
            image_url=article.image_url,
            category_id=article.category_id,
            deleted_at=datetime.now(timezone.utc),
        )
        self._session.add(deleted)

        stmt = update(Article).where(Article.id == article.id).values(is_deleted=True)
        await self._session.execute(stmt)
        await self._session.commit()

        logger.info(
            "ArticleRepository.soft_delete: archived original_id={original_id} deleted_id={deleted_id}",
            original_id=article.id,
            deleted_id=deleted.id if hasattr(deleted, "id") else None,
        )
