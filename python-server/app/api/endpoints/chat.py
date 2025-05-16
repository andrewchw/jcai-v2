from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class ChatMessage(BaseModel):
    """Schema for chat messages"""
    content: str
    role: str = "user"  # "user" or "assistant"


class ChatRequest(BaseModel):
    """Schema for incoming chat requests"""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for chat responses"""
    message: str
    conversation_id: str
    jira_references: Optional[List[dict]] = None


@router.post("/message", response_model=ChatResponse)
async def process_chat_message(chat_request: ChatRequest):
    """
    Process a chat message from the user.
    This will later be connected to the LLM via OpenRouter.
    """
    # This is a placeholder implementation
    # In the full implementation, we will:
    # 1. Process the message with the OpenRouter LLM
    # 2. Identify Jira-related intents
    # 3. If needed, call the MCP-Atlassian server
    # 4. Format and return the response
    
    return {
        "message": f"I received your message: '{chat_request.message}'. This is a placeholder response.",
        "conversation_id": chat_request.conversation_id or "new-conversation-id",
        "jira_references": []
    }
