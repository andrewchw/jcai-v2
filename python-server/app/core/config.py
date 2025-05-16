from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "JCAI - Jira Chatbot AI Assistant"
    PROJECT_DESCRIPTION: str = "A FastAPI server for the Jira Chatbot Edge Extension"
    VERSION: str = "0.1.0"
    
    # Environment settings
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]  # For development - restrict in production
    
    # MCP-Atlassian server settings
    MCP_SERVER_URL: str = "http://localhost:9000/sse"
    
    # OpenRouter API settings (for LLM)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "meta-llama/llama-3-8b-instruct"
    
    # SQLite database settings
    DATABASE_URL: str = "sqlite:///./jcai.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
    MCP_SERVER_URL: str = "http://localhost:9000/sse"  # For SSE transport
    
    # API Keys
    OPENROUTER_API_KEY: Optional[str] = None
    
    # SQLite settings
    SQLITE_DB_URL: str = "sqlite:///./jcai.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
