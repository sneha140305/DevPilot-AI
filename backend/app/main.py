from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging import logger, setup_logging

# Initialize logging
setup_logging()

# Initialize FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered code analysis, debugging and testing assistant.",
    version="0.1.0",
)


# Register API routes
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"]
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