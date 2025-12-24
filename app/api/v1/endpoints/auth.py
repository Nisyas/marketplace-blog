from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.repositories.user import UserRepository
from app.tasks.email_tasks import send_registration_email_task

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserRead:
    logger.info("Registration attempt: email={email}", email=email)

    user_in = UserCreate(email=email, password=password)
    existing_user = await user_repo.get_by_email(user_in.email)

    if existing_user is not None:
        logger.warning("Registration failed: email already exists email={email}", email=email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    hashed_password = get_password_hash(user_in.password)
    user = await user_repo.create(
        email=user_in.email,
        hashed_password=hashed_password,
    )

    logger.info("User registered successfully: user_id={user_id} email={email}", user_id=user.id, email=user.email)

    send_registration_email_task.delay(user.email)
    logger.debug("Registration email task enqueued for user_id={user_id} email={email}", user_id=user.id, email=user.email)

    return UserRead.model_validate(user)


@router.post("/login", response_model=UserRead)
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserRead:
    logger.info("Login attempt: email={email}", email=email)

    user_in = UserCreate(email=email, password=password)
    user = await user_repo.get_by_email(user_in.email)

    if user is None or not verify_password(user_in.password, user.hashed_password):
        logger.warning("Login failed: invalid credentials email={email}", email=email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(subject=user.id)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
    )

    logger.info("Login successful: user_id={user_id} email={email}", user_id=user.id, email=user.email)

    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie("access_token")
    logger.info("User logged out (access_token cookie deleted)")


@router.get("/me", response_model=UserRead)
async def read_current_user(request: Request) -> UserRead:
    user = getattr(request.state, "user", None)

    if user is None:
        logger.warning("Access to /auth/me without authenticated user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    logger.debug("Current user requested: user_id={user_id} email={email}", user_id=user.id, email=user.email)
    return UserRead.model_validate(user)
