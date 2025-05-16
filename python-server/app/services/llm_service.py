import aiohttp
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable

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
    
    async def generate_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "openrouter/auto",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        callback: Callable[[str], None] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming chat completion using OpenRouter API
        
        Args:
            messages: List of message objects with role and content
            model: Model ID to use
            max_tokens: Maximum tokens in the response
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system prompt to guide the model
            callback: Optional callback function to process each token
            
        Yields:
            Chunks of the streaming response
        """
        try:
            if not self.api_key:
                error_data = {"error": "OpenRouter API key not configured"}
                if callback:
                    callback(json.dumps(error_data))
                yield error_data
                return
            
            # Add system prompt if provided
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
                
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://jira-chatbot-extension",
                    "X-Title": "Jira Chatbot AI Assistant",
                    "Accept": "text/event-stream"
                }
                
                async with session.post(
                    f"{self.api_base_url}/chat/completions", 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_data = {"error": f"Failed to call OpenRouter API: {error_text}"}
                        if callback:
                            callback(json.dumps(error_data))
                        yield error_data
                        return
                    
                    # Process the SSE stream
                    buffer = ""
                    async for line in response.content:
                        if asyncio.current_task().cancelled():
                            logger.info("Streaming operation was cancelled")
                            return
                            
                        line_str = line.decode('utf-8')
                        buffer += line_str
                        
                        if buffer.endswith('\n\n'):
                            # SSE event completed
                            for event_data in buffer.strip().split('\n\n'):
                                if not event_data:
                                    continue
                                    
                                lines = event_data.split('\n')
                                data_lines = [l[6:] for l in lines if l.startswith('data: ')] 
                                
                                if data_lines:
                                    try:
                                        data_str = ''.join(data_lines)
                                        if data_str == '[DONE]':
                                            # Stream completed
                                            return
                                            
                                        data = json.loads(data_str)
                                        content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if content and callback:
                                            callback(content)
                                        yield data
                                    except json.JSONDecodeError as e:
                                        logger.error(f"Error parsing SSE data: {e}")
                            
                            buffer = ""
        
        except asyncio.CancelledError:
            logger.info("Streaming operation was cancelled")
            raise
        except Exception as e:
            error_data = {"error": f"Exception calling OpenRouter API: {str(e)}"}
            if callback:
                callback(json.dumps(error_data))
            yield error_data
            logger.exception(f"Exception calling OpenRouter API: {str(e)}")
