import sys
import os
from fastapi import FastAPI
import writer.serve
from app.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)



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
