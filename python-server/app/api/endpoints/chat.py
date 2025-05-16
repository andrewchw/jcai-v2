from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json

from app.services.chat_service import ChatService

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
    This endpoint uses the ChatService to process the message and return a response.
    """
    chat_service = ChatService()
    
    try:
        response = await chat_service.process_message(
            message=chat_request.message,
            conversation_id=chat_request.conversation_id
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/stream")
async def stream_chat_message(chat_request: ChatRequest):
    """
    Process a chat message with streaming response.
    This endpoint returns a streaming response with server-sent events.
    """
    chat_service = ChatService()
    
    async def event_generator():
        try:
            # Format for Server-Sent Events
            async for chunk in chat_service.process_message_stream(
                message=chat_request.message,
                conversation_id=chat_request.conversation_id
            ):
                # Prefix with 'data: ' and add a double newline to conform to SSE format
                yield f"data: {json.dumps(chunk)}\n\n"
                
            # Signal the end of the stream
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_data = {"error": f"Error streaming response: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
