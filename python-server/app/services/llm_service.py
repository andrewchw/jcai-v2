import aiohttp
import logging
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenRouterService:
    """Service for interacting with the OpenRouter API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.api_base_url = "https://openrouter.ai/api/v1"
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "openrouter/auto",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using OpenRouter API
        
        Args:
            messages: List of message objects with role and content
            model: Model ID to use
            max_tokens: Maximum tokens in the response
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system prompt to guide the model
            
        Returns:
            The API response as a dictionary
        """
        try:
            if not self.api_key:
                logger.error("OpenRouter API key not configured")
                return {"error": "OpenRouter API key not configured"}
            
            # Add system prompt if provided
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
                
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://jira-chatbot-extension", # Required by OpenRouter
                    "X-Title": "Jira Chatbot AI Assistant" # Required by OpenRouter
                }
                
                async with session.post(
                    f"{self.api_base_url}/chat/completions", 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error calling OpenRouter API: {error_text}")
                        return {"error": f"Failed to call OpenRouter API: {error_text}"}
                    
                    result = await response.json()
                    return result
        
        except Exception as e:
            logger.exception(f"Exception calling OpenRouter API: {str(e)}")
            return {"error": f"Exception calling OpenRouter API: {str(e)}"}
