from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

class Settings(BaseSettings):
    # Required fields for Supabase
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    
    # Required fields for Slack
    SLACK_BOT_TOKEN: str = Field(..., env="SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET: str = Field(..., env="SLACK_SIGNING_SECRET")
    
    # Required fields for Airtable
    AIRTABLE_API_KEY: str = Field(..., env="AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID: str = Field(..., env="AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME: str = Field(..., env="AIRTABLE_TABLE_NAME")

    # Required fields for SerpApi
    SERP_API_KEY: str = Field(..., env="SERP_API_KEY")

    # Writer API 
    WRITER_API_KEY: str = Field(..., env="WRITER_API_KEY")

    # Salesforce API credentials
    SALESFORCE_DOMAIN: str = Field(..., env="SALESFORCE_DOMAIN")
    SALESFORCE_USERNAME: str = Field(..., env="SALESFORCE_USERNAME")
    SALESFORCE_PASSWORD: str = Field(..., env="SALESFORCE_PASSWORD")
    SALESFORCE_SECURITY_TOKEN: str = Field(..., env="SALESFORCE_SECURITY_TOKEN")

    #Tavily API credentials
    TAVILY_API_KEY: str = Field(..., env="TAVILY_API_KEY")

    # Base URL for the application (Optional, set dynamically)
    BASE_URL: Optional[str] = None  # Excluded from validation during initialization

    def set_base_url(self, protocol: str = "http", host: str = "localhost", port: int = 8080):
        """
        Dynamically set the BASE_URL based on the protocol, host, and port.
        """
        self.BASE_URL = f"{protocol}://{host}:{port}/run"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore unknown fields

# Initialize settings and dynamically set BASE_URL
settings = Settings()
settings.set_base_url(
    protocol=os.getenv("PROTOCOL", "http"),
    host=os.getenv("HOST", "localhost"),
    port=int(os.getenv("PORT", 8080))
)
