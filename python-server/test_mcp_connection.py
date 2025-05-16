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

async def test_mcp_connection():
    """Test connection to MCP-Atlassian server and Jira Cloud"""
    
    # MCP server URL (SSE endpoint)
    mcp_url = "http://localhost:9000/sse"
    
    logger.info(f"Testing connection to MCP server at: {mcp_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test getting projects from Jira
            payload = {
                "name": "jira_get_projects",
                "parameters": {}
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            logger.info("Attempting to fetch Jira projects...")
            
            async with session.post(
                f"{mcp_url}/invoke", 
                json=payload, 
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error connecting to MCP: {error_text}")
                    return False
                
                result = await response.json()
                logger.info(f"Successfully connected to MCP. Found {len(result)} projects.")
                logger.info(f"First few projects: {result[:3]}")
                return True
    
    except Exception as e:
        logger.exception(f"Exception testing MCP connection: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("Starting MCP connection test...")
    
    try:
        result = asyncio.run(test_mcp_connection())
        
        if result:
            logger.info("✅ Connection test SUCCESSFUL!")
            logger.info("The MCP-Atlassian server is properly connected to Jira Cloud.")
        else:
            logger.error("❌ Connection test FAILED!")
            logger.error("Please check that:")
            logger.error("1. The MCP-Atlassian server is running")
            logger.error("2. Your Jira credentials in mcp-atlassian.env are correct")
            logger.error("3. OAuth setup has been completed correctly")
    
    except KeyboardInterrupt:
        logger.info("Test interrupted by user.")
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
