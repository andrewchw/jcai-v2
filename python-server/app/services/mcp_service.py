import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional

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
                
                # In a real implementation, we would use SSE to communicate with MCP server
                # This is a placeholder
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
                    return result
        
        except Exception as e:
            logger.exception(f"Exception calling MCP tool {tool_name}: {str(e)}")
            return {"error": f"Exception calling MCP tool: {str(e)}"}
    
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
