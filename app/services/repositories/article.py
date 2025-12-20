from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_

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
        return items, total

    async def get_by_id(self, article_id: int) -> Article | None:
        stmt = self._base_query().where(Article.id == article_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: ArticleCreate) -> Article:
        article = Article(
            title=data.title,
            content=data.content,
            category_id=data.category_id,
            image_url=data.image_url,
        )
        self._session.add(article)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(article)
        return article

    async def update(self, article: Article, data: ArticleUpdate) -> Article:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(article, field, value)
        await self._session.flush()
        await self._session.refresh(article)
        return article

    async def soft_delete(self, article: Article) -> None:
        deleted = DeletedArticle(
            original_id=article.id,
            title=article.title,
            content=article.content,
            image_url=article.image_url,
            category_id=article.category_id,
            deleted_at=datetime.now(tz=datetime.now().astimezone().tzinfo),
        )
        self._session.add(deleted)

        stmt = update(Article).where(Article.id == article.id).values(is_deleted=True)
        await self._session.execute(stmt)
