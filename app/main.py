import os

from fastapi import FastAPI, Request
from loguru import logger

from app.core.config import get_settings
from app.core.middleware import AuthMiddleware
from app.api.v1.endpoints import auth, categories, articles

settings = get_settings()

app = FastAPI(
    title="🦄Marketplace Blog API🦄",
    debug=settings.app_debug,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        "Incoming request: {method} {url} from {client}",
        method=request.method,
        url=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    response = await call_next(request)
    logger.info(
        "Completed request: {method} {url} -> {status_code}",
        method=request.method,
        url=request.url.path,
        status_code=response.status_code,
    )
    return response


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
    logger.info(
        "AuthMiddleware enabled",
        protected_paths=["/api/v1/articles", "/api/v1/categories", "/api/v1/auth/me"],
    )


@app.get("/health")
async def health_check():
    logger.debug("Health check requested", env=settings.app_env)
    return {"status": "ok", "env": settings.app_env}
