from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import os

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

class Settings(BaseSettings):
    # Required fields for Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Required fields for Slack
    SLACK_BOT_TOKEN: str
    SLACK_SIGNING_SECRET: str
    
    # Required fields for Airtable
    AIRTABLE_API_KEY: str
    AIRTABLE_BASE_ID: str
    AIRTABLE_TABLE_NAME: str

    # Required fields for SerpApi
    SERP_API_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore unknown fields

settings = Settings()
