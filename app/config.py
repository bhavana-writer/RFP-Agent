from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Required fields
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SLACK_BOT_TOKEN: str
    SLACK_SIGNING_SECRET: str
    AIRTABLE_API_KEY: str
    AIRTABLE_BASE_ID: str
    AIRTABLE_TABLE_NAME: str

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore unknown fields

settings = Settings()
