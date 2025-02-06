import sys
import os
from fastapi import FastAPI, Request
import writer.serve
from app.config import settings
import logging
from dotenv import load_dotenv
from string_block import JSONToString
from gong_block import GongIntegration



# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

JSONToString.register("workflows_jsontostring")
GongIntegration.register("workflows_gongintegration")


# Add the project root directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

print(settings.dict())  # Print loaded settings


# Import API router after adding the root directory to sys.path
from app.api.v1.endpoints.routes import api_router

# Access the FastAPI app provided by Writer
asgi_app: FastAPI = writer.serve.app

# Register API routes
asgi_app.include_router(api_router, prefix="/api/v1")

# Add a health check endpoint
@asgi_app.get("/healthcheck")
async def health_check():
    return {"status": "ok"}

# Initialize Base URL during startup
@asgi_app.middleware("http")
async def set_base_url_on_request(request: Request, call_next):
    """
    Middleware to set the base URL dynamically on every incoming request.
    """
    if not settings.BASE_URL:
        base_url = str(request.url).split(request.url.path)[0]
        settings.BASE_URL = base_url
    response = await call_next(request)
    return response