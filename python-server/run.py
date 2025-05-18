import logging
import uvicorn
import sys
from app.core.config import settings

# Configure logging
logging_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=logging_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Start the FastAPI server
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
