from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

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
    items, total = await repo.list_articles(
        search=search,
        category_id=category_id,
        page_number=page_number,
        page_size=page_size,
    )
    return ArticleListResponse(
        items=[ArticleRead.model_validate(a) for a in items],
        total=total,
        page_number=page_number,
        page_size=page_size,
    )


@router.post("/", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def create_article(
    title: str = File(...),
    content: str = File(...),
    category_id: int = File(...),
    image: UploadFile | None = File(default=None),
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleRead:
    image_url: str | None = None

    if image is not None:
        image_url = upload_image_file(
            file_obj=image.file,
            filename=image.filename,
            content_type=image.content_type,
        )

    article_in = ArticleCreate(
        title=title,
        content=content,
        category_id=category_id,
        image_url=image_url,
    )

    article = await repo.create(article_in)
    return ArticleRead.model_validate(article)


@router.get("/{article_id}", response_model=ArticleRead)
async def get_article(
    article_id: int,
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleRead:
    article = await repo.get_by_id(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )
    return ArticleRead.model_validate(article)


@router.put("/{article_id}", response_model=ArticleRead)
async def update_article(
    article_id: int,
    article_in: ArticleUpdate,
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleRead:
    article = await repo.get_by_id(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )

    article = await repo.update(article, article_in)
    return ArticleRead.model_validate(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    repo: ArticleRepository = Depends(get_article_repo),
) -> None:
    article = await repo.get_by_id(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )

    await repo.soft_delete(article)
