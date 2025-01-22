from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl
from typing import Optional
import os

# First, define the environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")  # Default to "local"

# Now we can use ENVIRONMENT in our debug prints
print(f"Current working directory: {os.getcwd()}")
print(f"Loading environment: {ENVIRONMENT}")
print(f"Looking for .env file in: {os.path.dirname(__file__)}")

# Then load the appropriate .env file
if ENVIRONMENT == "local":
    env_path = os.path.join(os.path.dirname(__file__), ".env.local")
else:
    env_path = os.path.join(os.path.dirname(__file__), ".env")

print(f"Attempting to load .env from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

# Load the environment file
if ENVIRONMENT == "local":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env.local"), override=True)
else:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

# Rest of the debug prints
print(f"Loading .env file from: {os.path.join(os.path.dirname(__file__), '.env')}")

class Settings(BaseSettings):
    # Required fields for Supabase
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    
    # Required fields for Slack
    SLACK_BOT_TOKEN: str = Field(..., env="SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET: str = Field(..., env="SLACK_SIGNING_SECRET")
    SLACK_USER_TOKEN: str = Field(..., env="SLACK_USER_TOKEN")
    
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

    # Tavily API credentials
    TAVILY_API_KEY: str = Field(..., env="TAVILY_API_KEY")

    # Base URL for the application (Optional, set dynamically)
    BASE_URL: Optional[str] = None

    # WordPress API Configuration with validation
    WORDPRESS_API_URL: HttpUrl = Field(
        ...,
        env="WORDPRESS_API_URL",
        description="WordPress REST API endpoint URL"
    )
    WORDPRESS_USERNAME: str = Field(
        ...,
        env="WORDPRESS_USERNAME",
        min_length=1,
        description="WordPress username for authentication"
    )
    WORDPRESS_APP_PASSWORD: str = Field(
        ...,
        env="WORDPRESS_APP_PASSWORD",
        min_length=8,
        description="WordPress application password for authentication"
    )

    def set_base_url(self):
        """
        Dynamically set the BASE_URL based on protocol, host, and port.
        """
        protocol = os.getenv("PROTOCOL", "http")
        host = os.getenv("HOST", "localhost")
        port = int(os.getenv("PORT", 8080))

        # Check if we're in a production environment
        environment = os.getenv("ENVIRONMENT", "local")

        # For production with HTTPS, omit the port
        if environment == "production" and protocol == "https":
            self.BASE_URL = f"{protocol}://{host}/run"
        # For local or other environments, include the port
        elif (protocol == "http" and port != 80) or (protocol == "https" and port != 443):
            self.BASE_URL = f"{protocol}://{host}:{port}/run"
        else:
            self.BASE_URL = f"{protocol}://{host}/run"

        print(f"Base URL set to: {self.BASE_URL}")


    class Config:
        env_file = ".env"  # Default fallback
        extra = "ignore"  # Ignore unknown fields

# Initialize settings
settings = Settings()
settings.set_base_url()
print("Settings loaded successfully")

