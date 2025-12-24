from fastapi import APIRouter, Depends, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryRead
from app.services.repositories.category import CategoryRepository

router = APIRouter(prefix="/categories", tags=["categories"])


def get_category_repo(db: AsyncSession = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(...),
    slug: str = Form(...),
    description: str | None = Form(default=None),
    repo: CategoryRepository = Depends(get_category_repo),
) -> CategoryRead:
    logger.info("Creating category: name={name} slug={slug}", name=name, slug=slug)

    category_in = CategoryCreate(name=name, slug=slug, description=description)
    category = await repo.create(category_in)

    logger.info(
        "Category created: id={id} name={name} slug={slug}",
        id=category.id,
        name=category.name,
        slug=category.slug,
    )

    return CategoryRead.model_validate(category)


@router.get("/", response_model=list[CategoryRead])
async def list_categories(
    repo: CategoryRepository = Depends(get_category_repo),
) -> list[CategoryRead]:
    logger.debug("Listing categories")
    categories = await repo.list_all()
    logger.debug("Categories fetched: count={count}", count=len(categories))
    return [CategoryRead.model_validate(c) for c in categories]
