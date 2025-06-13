"""
LLM Service for OpenRouter API integration.

This service handles natural language processing for Jira operations
using OpenRouter's API with various LLM models.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator

import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with OpenRouter LLM API."""

    def __init__(self):
        """Initialize the LLM service with OpenRouter configuration."""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.default_model = os.getenv("DEFAULT_LLM_MODEL", "meta-llama/llama-3-8b-instruct")
        self.fallback_model = os.getenv("FALLBACK_LLM_MODEL", "openai/gpt-3.5-turbo")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        self.cache_ttl_hours = int(os.getenv("LLM_CACHE_TTL_HOURS", "24"))

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Jira Chatbot Extension"
        }

        # Cache for responses
        self._cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"LLM Service initialized with model: {self.default_model}")

    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt and model combination."""
        import hashlib
        content = f"{prompt}:{model}:{self.temperature}:{self.max_tokens}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cached response is still valid."""
        expiry = timestamp + timedelta(hours=self.cache_ttl_hours)
        return datetime.now() < expiry

    async def _make_request(self, payload: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Make HTTP request to OpenRouter API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error ({e.response.status_code}): {e.response.text}")
            if model == self.default_model and model != self.fallback_model:
                logger.info(f"Falling back to {self.fallback_model}")
                payload["model"] = self.fallback_model
                return await self._make_request(payload, self.fallback_model)
            raise HTTPException(status_code=503, detail=f"LLM service unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"LLM processing error: {str(e)}")

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: User input prompt
            system_prompt: System context prompt
            model: LLM model to use (defaults to configured model)
            use_cache: Whether to use response caching

        Returns:
            Generated response text
        """
        # Ensure model is not None
        effective_model: str = model if model is not None else self.default_model

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(prompt, effective_model)
            if cache_key in self._cache:
                cached_item = self._cache[cache_key]
                if self._is_cache_valid(cached_item["timestamp"]):
                    logger.debug(f"Using cached response for prompt: {prompt[:50]}...")
                    return cached_item["response"]
                else:
                    del self._cache[cache_key]        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": effective_model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }

        logger.debug(f"LLM request - Model: {effective_model}, Prompt: {prompt[:100]}...")

        response_data = await self._make_request(payload, effective_model)

        if "choices" not in response_data or not response_data["choices"]:
            raise HTTPException(status_code=500, detail="Invalid response from LLM service")

        response_text = response_data["choices"][0]["message"]["content"]

        # Cache the response
        if use_cache:
            cache_key = self._get_cache_key(prompt, effective_model)
            self._cache[cache_key] = {
                "response": response_text,
                "timestamp": datetime.now()
            }

        logger.info(f"LLM response generated successfully (length: {len(response_text)})")
        return response_text

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the LLM for real-time chat.

        Args:
            prompt: User input prompt
            system_prompt: System context prompt
            model: LLM model to use

        Yields:
            Response chunks as they arrive
        """
        if not model:
            model = self.default_model

        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True
        }

        logger.debug(f"LLM streaming request - Model: {model}, Prompt: {prompt[:100]}...")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data.strip() == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"LLM streaming failed: {str(e)}")
            yield f"Error: {str(e)}"

    def get_jira_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get system prompt for Jira operations.

        Args:
            user_context: Optional user context (projects, recent issues, etc.)

        Returns:
            System prompt for Jira operations
        """
        base_prompt = """You are a helpful Jira assistant integrated into a Microsoft Edge extension.
You help users manage Jira issues and tasks through natural language commands.

CAPABILITIES:
- Create new Jira issues/tasks
- Search and query existing issues
- Update issue status, assignee, priority, due dates
- Add comments to issues
- View project information

RESPONSE FORMAT:
Always respond with a JSON object containing:
{
    "action": "create_issue|search_issues|update_issue|add_comment|get_projects|clarify",
    "parameters": {
        // Action-specific parameters
    },
    "message": "Human-readable response to user",
    "confidence": 0.0-1.0
}

ACTIONS:
1. create_issue: Create new Jira issue
   - Required: summary, project_key
   - Optional: description, assignee, priority, due_date, issue_type

2. search_issues: Search for existing issues
   - Optional: assignee, project, status, text_search, due_date_filter

3. update_issue: Update existing issue
   - Required: issue_key
   - Optional: status, assignee, priority, due_date, summary, description

4. add_comment: Add comment to issue
   - Required: issue_key, comment

5. get_projects: Get available projects
   - No parameters required

6. clarify: Ask for clarification when request is ambiguous
   - Required: question

EXAMPLES:
User: "Create a task for John to review docs by Friday"
Response: {
    "action": "create_issue",
    "parameters": {
        "summary": "Review documentation",
        "assignee": "John",
        "due_date": "2025-06-13",
        "project_key": "JCAI"
    },
    "message": "I'll create a task for John to review documentation by Friday.",
    "confidence": 0.9
}

User: "What tasks are assigned to me?"
Response: {
    "action": "search_issues",
    "parameters": {
        "assignee": "currentUser"
    },
    "message": "Let me find all tasks assigned to you.",
    "confidence": 1.0
}"""

        if user_context:
            if "projects" in user_context:
                projects = ", ".join([f"{p['key']} ({p['name']})" for p in user_context["projects"]])
                base_prompt += f"\n\nAVAILABLE PROJECTS: {projects}"

            if "default_project" in user_context:
                base_prompt += f"\nDEFAULT PROJECT: {user_context['default_project']}"

        return base_prompt

    async def process_jira_command(
        self,
        user_input: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language Jira command.

        Args:
            user_input: User's natural language input
            user_context: Context about user's projects, recent issues, etc.

        Returns:
            Parsed command with action and parameters
        """
        system_prompt = self.get_jira_system_prompt(user_context)

        try:
            response = await self.generate_response(
                prompt=user_input,
                system_prompt=system_prompt,
                use_cache=False  # Don't cache Jira commands as context may change
            )

            # Try to parse JSON response
            try:
                parsed_response = json.loads(response)
                if not isinstance(parsed_response, dict) or "action" not in parsed_response:
                    raise ValueError("Invalid response format")
                return parsed_response

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                # Fallback response
                return {
                    "action": "clarify",
                    "parameters": {
                        "question": "I didn't understand that request. Could you please rephrase it?"
                    },
                    "message": "I'm having trouble understanding your request. Could you please be more specific?",
                    "confidence": 0.1
                }

        except Exception as e:
            logger.error(f"Error processing Jira command: {str(e)}")
            return {
                "action": "clarify",
                "parameters": {
                    "question": "I encountered an error processing your request. Please try again."
                },
                "message": "Sorry, I encountered an error. Please try your request again.",
                "confidence": 0.0
            }

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
        logger.info("LLM response cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        valid_entries = sum(
            1 for item in self._cache.values()
            if self._is_cache_valid(item["timestamp"])
        )

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._cache) - valid_entries,
            "cache_ttl_hours": self.cache_ttl_hours
        }


# Global LLM service instance
llm_service = LLMService()
