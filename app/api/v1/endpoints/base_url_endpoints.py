from fastapi import APIRouter, Request, HTTPException
from app.config import settings

router = APIRouter()


@router.get("/")
async def get_base_url():
    """
    Retrieve the current base URL.
    """
    return {"base_url": settings.BASE_URL}


@router.post("/")
async def set_base_url(request: Request):
    """
    Dynamically set the base URL from the incoming request.
    """
    try:
        # Extract base URL from the incoming request
        base_url = str(request.url).split(request.url.path)[0]  # Strips the path to get the root URL
        settings.BASE_URL = base_url
        return {"message": "Base URL updated successfully.", "base_url": settings.BASE_URL}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
