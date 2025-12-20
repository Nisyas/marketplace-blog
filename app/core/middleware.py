from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, protected_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.protected_paths = protected_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.user = None

        path = request.url.path
        if not self._is_protected_path(path):
            return await call_next(request)

        token = request.cookies.get("access_token")
        if not token:
            return JSONResponse(
                status_code=401, content={"detail": "Not authenticated"}
            )

        payload = decode_access_token(token)
        if payload is None:
            return JSONResponse(
                status_code=401, content={"detail": "Invalid or expired token"}
            )

        user_id = payload.get("sub")
        if user_id is None:
            return JSONResponse(
                status_code=401, content={"detail": "Invalid token payload"}
            )

        async with AsyncSessionLocal() as session:
            user = await self._get_user(session, int(user_id))

        if user is None or not user.is_active:
            return JSONResponse(
                status_code=401, content={"detail": "User not found or inactive"}
            )

        request.state.user = user

        response = await call_next(request)
        return response

    def _is_protected_path(self, path: str) -> bool:
        if not self.protected_paths:
            return True
        return any(path.startswith(prefix) for prefix in self.protected_paths)

    @staticmethod
    async def _get_user(session, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
