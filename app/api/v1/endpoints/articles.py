from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from fastapi import UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.session import get_db
from app.services.storage import upload_image_file
from app.schemas.article import (
    ArticleCreate,
    ArticleListResponse,
    ArticleRead,
    ArticleUpdate,
)
from app.services.repositories.article import ArticleRepository

router = APIRouter(prefix="/articles", tags=["articles"])


def get_article_repo(db: AsyncSession = Depends(get_db)) -> ArticleRepository:
    return ArticleRepository(db)


@router.get("/", response_model=ArticleListResponse)
async def list_articles(
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    page_number: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleListResponse:
    logger.debug(
        "Listing articles: search={search} category_id={category_id} page_number={page_number} page_size={page_size}",
        search=search,
        category_id=category_id,
        page_number=page_number,
        page_size=page_size,
    )

    items, total = await repo.list_articles(
        search=search,
        category_id=category_id,
        page_number=page_number,
        page_size=page_size,
    )

    logger.debug(
        "Articles fetched: total={total} page_number={page_number} page_size={page_size} returned={returned}",
        total=total,
        page_number=page_number,
        page_size=page_size,
        returned=len(items),
    )

    return ArticleListResponse(
        items=[ArticleRead.model_validate(a) for a in items],
        total=total,
        page_number=page_number,
        page_size=page_size,
    )


@router.post("/", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def create_article(
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(...),
    image: UploadFile | None = File(default=None),
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleRead:
    logger.info(
        "Creating article: title={title} category_id={category_id} has_image={has_image}",
        title=title,
        category_id=category_id,
        has_image=image is not None,
    )

    image_url: str | None = None
    if image is not None:
        try:
            image_url = upload_image_file(
                file_obj=image.file,
                filename=image.filename,
                content_type=image.content_type,
            )
            logger.debug(
                "Image uploaded for article: filename={filename} url={url}",
                filename=image.filename,
                url=image_url,
            )
        except ValueError as e:
            logger.warning(
                "Invalid image upload for article: filename={filename} error={error}",
                filename=image.filename,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        except RuntimeError as e:
            logger.error(
                "Storage error during image upload: filename={filename} error={error}",
                filename=image.filename,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to upload image to storage",
            ) from e

    article_in = ArticleCreate(
        title=title,
        content=content,
        category_id=category_id,
        image_url=image_url,
    )

    article = await repo.create(article_in)

    logger.info(
        "Article created: id={id} title={title} category_id={category_id}",
        id=article.id,
        title=article.title,
        category_id=article.category_id,
    )

    return ArticleRead.model_validate(article)


@router.get("/{article_id}", response_model=ArticleRead)
async def get_article(
    article_id: int,
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleRead:
    logger.debug("Fetching article: id={id}", id=article_id)

    article = await repo.get_by_id(article_id)
    if article is None:
        logger.warning("Article not found: id={id}", id=article_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )

    logger.debug(
        "Article fetched: id={id} title={title}", id=article.id, title=article.title
    )
    return ArticleRead.model_validate(article)


@router.put("/{article_id}", response_model=ArticleRead)
async def update_article(
    article_id: int,
    article_in: ArticleUpdate,
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleRead:
    logger.info("Updating article: id={id}", id=article_id)

    article = await repo.get_by_id(article_id)
    if article is None:
        logger.warning("Update failed: article not found id={id}", id=article_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )

    article = await repo.update(article, article_in)

    logger.info(
        "Article updated: id={id} title={title}", id=article.id, title=article.title
    )
    return ArticleRead.model_validate(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    repo: ArticleRepository = Depends(get_article_repo),
) -> None:
    logger.info("Soft-deleting article: id={id}", id=article_id)

    article = await repo.get_by_id(article_id)
    if article is None:
        logger.warning("Delete failed: article not found id={id}", id=article_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )

    await repo.soft_delete(article)
    logger.info("Article soft-deleted: id={id}", id=article_id)
