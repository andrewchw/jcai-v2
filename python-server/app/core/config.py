import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    # API settings
    API_HOST: str = os.getenv("API_HOST", "localhost")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    SITE_URL: str = os.getenv("SITE_URL", "http://localhost:8000")
    
    # Jira settings
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_USERNAME: str = os.getenv("JIRA_USERNAME", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    DEFAULT_JIRA_PROJECT_KEY: str = os.getenv("DEFAULT_JIRA_PROJECT_KEY", "")
    
    # OAuth 2.0 settings for Jira
    JIRA_OAUTH_CLIENT_ID: str = os.getenv("JIRA_OAUTH_CLIENT_ID", "")
    JIRA_OAUTH_CLIENT_SECRET: str = os.getenv("JIRA_OAUTH_CLIENT_SECRET", "")
    JIRA_OAUTH_CALLBACK_URL: str = os.getenv("JIRA_OAUTH_CALLBACK_URL", "")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # Memory settings
    MEMORY_PATH: str = os.getenv("MEMORY_PATH", "./memory.jsonl")
    USE_FALLBACK_MEMORY: bool = os.getenv("USE_FALLBACK_MEMORY", "True").lower() == "true"
    
    # Reminder settings
    REMINDER_CHECK_INTERVAL: int = int(os.getenv("REMINDER_CHECK_INTERVAL", "300"))
    
    # Debug settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").lower()

# Create a settings object
settings = Settings()
