from fastapi import APIRouter
from app.api.v1.endpoints import slack_endpoints, airtable_endpoints

api_router = APIRouter()

# Include Slack-related endpoints
api_router.include_router(slack_endpoints.router, prefix="/slack", tags=["slack"])
api_router.include_router(airtable_endpoints.router, prefix="/airtable", tags=["airtable"])



