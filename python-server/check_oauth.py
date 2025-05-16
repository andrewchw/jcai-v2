import asyncio
import aiohttp
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def check_oauth_status():
    """Check OAuth token status for MCP-Atlassian server"""
    
    # MCP server URL (SSE endpoint)
    mcp_url = "http://localhost:9000/sse"
    
    logger.info(f"Checking OAuth status using MCP server at: {mcp_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Try to get the current user to test OAuth token
            payload = {
                "name": "jira_get_myself",
                "parameters": {}
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            logger.info("Attempting to fetch current user from Jira...")
            
            async with session.post(
                f"{mcp_url}/invoke", 
                json=payload, 
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error checking OAuth: {error_text}")
                    return False
                
                result = await response.json()
                logger.info(f"OAuth check successful!")
                logger.info(f"Logged in as: {result.get('displayName', 'Unknown')} ({result.get('emailAddress', 'No email')})")
                return True
    
    except Exception as e:
        logger.exception(f"Exception checking OAuth: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("Starting OAuth status check...")
    
    try:
        result = asyncio.run(check_oauth_status())
        
        if result:
            logger.info("✅ OAuth check SUCCESSFUL!")
            logger.info("Your OAuth token is valid and you are properly authenticated to Jira Cloud.")
        else:
            logger.error("❌ OAuth check FAILED!")
            logger.error("Please check that:")
            logger.error("1. You've completed the OAuth setup using ./setup-oauth.ps1")
            logger.error("2. The MCP-Atlassian server is running with SSE transport")
            logger.error("3. Your OAuth credentials in mcp-atlassian.env are correct")
    
    except KeyboardInterrupt:
        logger.info("Check interrupted by user.")
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
