from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[User]:
        stmt = select(User)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, *, email: str, hashed_password: str) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(user)
        return user
