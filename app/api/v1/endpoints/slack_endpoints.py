from fastapi import APIRouter, Request
from app.services.slack_service import slack_handler
from app.services.slack_service import logger

router = APIRouter()

@router.post("/events")
async def slack_events(request: Request):
    body = await request.json()
    logger.info(f"Raw event received: {body}")  # Log the raw event
    print(f"DEBUG: Raw event received - {body}")  # Fallback print
    return await slack_handler.handle(request)
