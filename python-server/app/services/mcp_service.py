import aiohttp
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable

from app.core.config import settings

logger = logging.getLogger(__name__)


class MCPAtlassianService:
    """Service for interacting with the MCP-Atlassian server"""
    
    def __init__(self, mcp_server_url: str = None):
        self.mcp_server_url = mcp_server_url or settings.MCP_SERVER_URL
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP-Atlassian server
        
        Args:
            tool_name: The name of the tool to call
            parameters: The parameters to pass to the tool
            
        Returns:
            The tool response as a dictionary
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "name": tool_name,
                    "parameters": parameters
                }
                
                headers = {
                    "Content-Type": "application/json"
                }
                
                logger.info(f"Calling MCP tool {tool_name} with parameters: {parameters}")
                
                # Call the MCP server invoke endpoint using SSE
                async with session.post(
                    f"{self.mcp_server_url}/invoke", 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error calling MCP tool {tool_name}: {error_text}")
                        return {"error": f"Failed to call MCP tool: {error_text}"}
                    
                    result = await response.json()
                    logger.debug(f"Received response from MCP tool {tool_name}: {result}")
                    return result
        
        except Exception as e:
            logger.exception(f"Exception calling MCP tool {tool_name}: {str(e)}")
            return {"error": f"Exception calling MCP tool: {str(e)}"}
            
    async def stream_call_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        callback: Callable[[Dict[str, Any]], None] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Call a tool on the MCP-Atlassian server with streaming response
        
        Args:
            tool_name: The name of the tool to call
            parameters: The parameters to pass to the tool
            callback: Optional callback function to process each chunk
            
        Yields:
            Each chunk of the streaming response
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "name": tool_name,
                    "parameters": parameters,
                    "stream": True
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
                
                logger.info(f"Streaming MCP tool {tool_name} with parameters: {parameters}")
                
                # Stream response using SSE
                async with session.post(
                    f"{self.mcp_server_url}/invoke", 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_data = {"error": f"Failed to call MCP tool: {error_text}"}
                        if callback:
                            callback(error_data)
                        yield error_data
                        return
                    
                    # Process the SSE stream
                    buffer = ""
                    async for line in response.content:
                        line_str = line.decode('utf-8')
                        buffer += line_str
                        
                        if buffer.endswith('\n\n'):
                            # SSE event completed
                            for event_data in buffer.strip().split('\n\n'):
                                if not event_data:
                                    continue
                                    
                                lines = event_data.split('\n')
                                data_lines = [l[5:] for l in lines if l.startswith('data:')]
                                
                                if data_lines:
                                    try:
                                        data_str = ''.join(data_lines)
                                        if data_str == '[DONE]':
                                            # Stream completed
                                            return
                                            
                                        data = json.loads(data_str)
                                        if callback:
                                            callback(data)
                                        yield data
                                    except json.JSONDecodeError as e:
                                        logger.error(f"Error parsing SSE data: {e}")
                            
                            buffer = ""
        
        except asyncio.CancelledError:
            logger.info(f"Streaming operation for {tool_name} was cancelled")
            raise
        except Exception as e:
            error_data = {"error": f"Exception in streaming MCP tool: {str(e)}"}
            if callback:
                callback(error_data)
            yield error_data
            logger.exception(f"Exception streaming MCP tool {tool_name}: {str(e)}")
    
    async def get_jira_issues(
        self,
        jql: str,
        max_results: int = 20,
        fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Search for Jira issues using JQL
        
        Args:
            jql: The JQL query string
            max_results: Maximum number of results to return
            fields: List of fields to include in the results
            
        Returns:
            The issues found by the search
        """
        parameters = {
            "jql": jql,
            "maxResults": max_results
        }
        
        if fields:
            parameters["fields"] = fields
            
        return await self.call_tool("jira_search", parameters)
    
    async def create_jira_issue(
        self,
        project_key: str,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
        assignee: Optional[str] = None,
        fields: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new Jira issue
        
        Args:
            project_key: The project key (e.g., "PROJ")
            summary: Issue summary
            description: Issue description
            issue_type: Issue type (e.g., "Task", "Bug")
            assignee: Username of the assignee
            fields: Additional fields for the issue
            
        Returns:
            The created issue data
        """
        parameters = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type}
            }
        }
        
        if assignee:
            parameters["fields"]["assignee"] = {"name": assignee}
            
        if fields:
            parameters["fields"].update(fields)
            
        return await self.call_tool("jira_create_issue", parameters)
