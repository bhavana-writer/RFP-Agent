from fastapi import APIRouter
from app.api.v1.endpoints import slack_endpoints, airtable_endpoints, google_trends_endpoints, salesforce_endpoints, writer_endpoints, base_url_endpoints, tavily_endpoints

api_router = APIRouter()

# Include Slack-related endpoints
api_router.include_router(slack_endpoints.router, prefix="/slack", tags=["slack"])
api_router.include_router(airtable_endpoints.router, prefix="/airtable", tags=["airtable"])
api_router.include_router(google_trends_endpoints.router, prefix="/google-trends", tags=["google_trends"])
api_router.include_router(salesforce_endpoints.router, prefix="/salesforce", tags=["salesforce"])
api_router.include_router(writer_endpoints.router, prefix="/writer", tags=["writer"])
api_router.include_router(base_url_endpoints.router, prefix="/base-url", tags=["base_url"])
api_router.include_router(tavily_endpoints.router, prefix="/tavily", tags=["Tavily"])





