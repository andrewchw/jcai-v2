from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class Message(BaseModel):
    """Schema for a chat message"""
    content: str
    role: str  # "user", "assistant", or "system"
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "content": "Create a task for updating documentation",
                "role": "user", 
                "timestamp": "2025-05-16T14:30:00Z"
            }
        }


class Conversation(BaseModel):
    """Schema for a conversation"""
    id: str
    messages: List[Message]
    user_id: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": "conv_123456789",
                "messages": [
                    {
                        "content": "How can I help you today?",
                        "role": "assistant",
                        "timestamp": "2025-05-16T14:29:00Z"
                    },
                    {
                        "content": "Create a task for updating documentation",
                        "role": "user",
                        "timestamp": "2025-05-16T14:30:00Z"
                    }
                ],
                "user_id": "user_123",
                "created_at": "2025-05-16T14:29:00Z",
                "updated_at": "2025-05-16T14:30:00Z"
            }
        }
