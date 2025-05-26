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
    DEFAULT_JIRA_PROJECT_KEY: str = os.getenv(
        "DEFAULT_JIRA_PROJECT_KEY", ""
    )  # OAuth 2.0 settings for Jira
    JIRA_OAUTH_CLIENT_ID: str = os.getenv("JIRA_OAUTH_CLIENT_ID", "")
    JIRA_OAUTH_CLIENT_SECRET: str = os.getenv("JIRA_OAUTH_CLIENT_SECRET", "")
    JIRA_OAUTH_CALLBACK_URL: str = os.getenv("JIRA_OAUTH_CALLBACK_URL", "")
    ATLASSIAN_OAUTH_CLOUD_ID: str = os.getenv("ATLASSIAN_OAUTH_CLOUD_ID", "")
    ATLASSIAN_OAUTH_SCOPE: str = os.getenv(
        "ATLASSIAN_OAUTH_SCOPE", "read:jira-work write:jira-work offline_access"
    )
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # LLM Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv(
        "DEFAULT_LLM_MODEL", "meta-llama/llama-3-8b-instruct"
    )
    FALLBACK_LLM_MODEL: str = os.getenv("FALLBACK_LLM_MODEL", "openai/gpt-3.5-turbo")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    LLM_CACHE_TTL_HOURS: int = int(os.getenv("LLM_CACHE_TTL_HOURS", "24"))

    # Memory settings
    MEMORY_PATH: str = os.getenv("MEMORY_PATH", "./memory.jsonl")
    USE_FALLBACK_MEMORY: bool = (
        os.getenv("USE_FALLBACK_MEMORY", "True").lower() == "true"
    )

    # Reminder settings
    REMINDER_CHECK_INTERVAL: int = int(os.getenv("REMINDER_CHECK_INTERVAL", "300"))

    # Debug settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").lower()


# Create a settings object
settings = Settings()
