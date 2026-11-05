from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import review, test_generation
from app.api.routes.analysis import router as analysis_router
from app.api.routes.health import router as health_router
from app.api.routes.uploads import router as uploads_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.db.database import initialize_database

# Initialize logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize application resources during startup.
    """

    initialize_database()

    yield

# Initialize FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered code analysis, debugging and testing assistant.",
    version="0.1.0",
    lifespan=lifespan,
)


# Register API routes
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"]
)

app.include_router(
    uploads_router,
    prefix="/api/v1",
    tags=["Uploads"],
)

app.include_router(
    analysis_router,
    prefix="/api/v1",
    tags=["Analysis"],
)

app.include_router(
    review.router,
    prefix="/api/v1",
)

app.include_router(
    test_generation.router,
    prefix="/api/v1",
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    logger.exception(
        "Unhandled exception occurred: %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred."
            }
        }
    )


@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Welcome to DevPilot AI API",
        "version": "0.1.0"
    }