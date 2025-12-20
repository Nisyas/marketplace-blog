from fastapi import FastAPI
import os

from app.core.config import get_settings
from app.core.middleware import AuthMiddleware
from app.api.v1.endpoints import auth, categories, articles


settings = get_settings()

app = FastAPI(
    title="🦄Marketplace Blog API🦄",
    debug=settings.app_debug,
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(articles.router, prefix="/api/v1")
if not os.getenv("TESTING"):
    app.add_middleware(
        AuthMiddleware,
        protected_paths=[
            "/api/v1/articles",
            "/api/v1/categories",
            "/api/v1/auth/me",
        ],
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}
