from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        logger.debug("UserRepository.get_by_id: user_id={user_id}", user_id=user_id)
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            logger.debug(
                "UserRepository.get_by_id: user not found user_id={user_id}",
                user_id=user_id,
            )
        else:
            logger.debug(
                "UserRepository.get_by_id: user found user_id={user_id}",
                user_id=user.id,
            )
        return user

    async def get_by_email(self, email: str) -> User | None:
        logger.debug("UserRepository.get_by_email: email={email}", email=email)
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            logger.debug(
                "UserRepository.get_by_email: user not found email={email}", email=email
            )
        else:
            logger.debug(
                "UserRepository.get_by_email: user found user_id={user_id} email={email}",
                user_id=user.id,
                email=user.email,
            )
        return user

    async def list_all(self) -> Sequence[User]:
        logger.debug("UserRepository.list_all called")
        stmt = select(User)
        result = await self._session.execute(stmt)
        users = result.scalars().all()
        logger.debug("UserRepository.list_all: count={count}", count=len(users))
        return users

    async def create(self, *, email: str, hashed_password: str) -> User:
        logger.info("UserRepository.create: email={email}", email=email)
        user = User(
            email=email,
            hashed_password=hashed_password,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        logger.info(
            "UserRepository.create: created user_id={user_id} email={email}",
            user_id=user.id,
            email=user.email,
        )
        return user
