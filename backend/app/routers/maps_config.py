from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/config", tags=["Config"])

@router.get("/maps-key")
def get_maps_key():
    return {"key": settings.GOOGLE_MAPS_API_KEY}