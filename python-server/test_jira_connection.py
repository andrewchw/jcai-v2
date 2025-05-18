import asyncio
import os
import logging
import sys
from dotenv import load_dotenv
from atlassian import Jira

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_jira_connection():
    """Test connection to Jira Cloud using Atlassian Python API"""
    
    # Get Jira credentials from environment
    jira_url = os.getenv("JIRA_URL")
    jira_username = os.getenv("JIRA_USERNAME")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_username, jira_api_token]):
        logger.error("Jira credentials not found in environment variables")
        return False
    
    logger.info(f"Testing connection to Jira at: {jira_url}")
    
    try:
        # Initialize Jira client
        jira = Jira(
            url=jira_url,
            username=jira_username,
            password=jira_api_token,
            cloud=True
        )
        
        # Test connection by getting current user
        logger.info("Attempting to fetch current user...")
        myself = jira.myself()
        
        if not myself:
            logger.error("Could not get current user data")
            return False
        
        logger.info(f"Successfully connected as: {myself.get('displayName')} ({myself.get('emailAddress')})")
        
        # Test getting projects
        logger.info("Fetching projects...")
        projects = jira.projects()
        
        if not projects:
            logger.warning("No projects found or couldn't fetch projects")
        else:
            logger.info(f"Successfully fetched {len(projects)} projects")
            project_keys = [p.get('key') for p in projects[:5]]
            logger.info(f"Sample project keys: {', '.join(project_keys)}")
        
        return True
    
    except Exception as e:
        logger.exception(f"Exception testing Jira connection: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("Starting Jira API connection test...")
    
    try:
        result = asyncio.run(test_jira_connection())
        
        if result:
            logger.info("✅ Connection test SUCCESSFUL!")
            logger.info("The Atlassian Python API is properly connected to Jira Cloud.")
        else:
            logger.error("❌ Connection test FAILED!")
            logger.error("Please check that:")
            logger.error("1. Your Jira credentials in .env are correct")
            logger.error("2. You have the necessary permissions in Jira")
            logger.error("3. Your network allows connections to Jira Cloud")
    
    except KeyboardInterrupt:
        logger.info("Test interrupted by user.")
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
