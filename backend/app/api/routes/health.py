from fastapi import APIRouter

from app.core.config import settings


router = APIRouter()


@router.get("/health")
async def health_check():

    return {
        "success": True,
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV
    }