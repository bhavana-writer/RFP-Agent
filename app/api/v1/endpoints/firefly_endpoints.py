from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.firefly_service import FireflyService

router = APIRouter()
firefly_service = FireflyService()

class ImageRequest(BaseModel):
    prompt: str

@router.post("/generate-image/")
async def generate_image(request: ImageRequest):
    """
    Generate an image from a text prompt using the Firefly API.
    """
    try:
        result = firefly_service.generate_image(request.prompt)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        image_url = result['outputs'][0]['image']['url']
        return {"image_url": image_url}
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve image URL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
