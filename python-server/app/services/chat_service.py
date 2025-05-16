from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.chat import Conversation, Message
from app.services.mcp_service import MCPAtlassianService
from app.services.llm_service import OpenRouterService


class ChatService:
    """Service for managing chat conversations and processing messages"""
    
    def __init__(self):
        self.mcp_service = MCPAtlassianService()
        self.llm_service = OpenRouterService()
        
        # In-memory storage of active conversations
        # In a production environment, this would be stored in a database
        self._conversations: Dict[str, Conversation] = {}
        
    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response
        
        Args:
            message: The user's message
            conversation_id: Optional ID of an existing conversation
            user_id: Optional user ID
            
        Returns:
            A dictionary containing the assistant's response and conversation info
        """
        # Get or create conversation
        conversation = self._get_or_create_conversation(conversation_id, user_id)
        
        # Add user message to conversation
        timestamp = datetime.utcnow().isoformat() + "Z"
        user_message = Message(content=message, role="user", timestamp=timestamp)
        conversation.messages.append(user_message)
        
        # Update conversation timestamp
        conversation.updated_at = timestamp
        
        # Extract the messages for the LLM (excluding system messages)
        chat_messages = [{"role": msg.role, "content": msg.content} 
                       for msg in conversation.messages[-10:]]  # Only use last 10 messages
        
        # Add a system prompt for Jira context
        system_prompt = """You are a helpful AI assistant for Jira tasks. You can help with:
1. Creating new issues
2. Updating existing issues
3. Searching for issues
4. Adding comments to issues
5. Explaining Jira concepts

When asked to perform Jira operations, provide clear, accurate responses
with the relevant Jira issue keys and summaries."""

        try:
            # Use LLM to determine intent and generate a response
            response = await self.llm_service.generate_chat_completion(
                messages=chat_messages,
                model="anthropic/claude-3-sonnet",  # Use a capable model
                max_tokens=1000,
                system_prompt=system_prompt
            )
            
            if "error" in response:
                logger.error(f"Error from LLM: {response['error']}")
                assistant_content = f"I'm sorry, but I encountered an error: {response['error']}"
            else:
                assistant_content = response["choices"][0]["message"]["content"]
                
                # Check for Jira references in the message
                jira_references = []
                
                # Simple extraction of Jira issue references (e.g., PROJECT-123)
                # Could be enhanced with more sophisticated extraction
                import re
                issue_matches = re.findall(r'([A-Z]+-\d+)', assistant_content)
                if issue_matches:
                    # Get issue details from Jira
                    for issue_key in issue_matches:
                        try:
                            issue_details = await self.mcp_service.call_tool(
                                "jira_get_issue",
                                {"issue_key": issue_key}
                            )
                            if "error" not in issue_details:
                                jira_references.append({
                                    "key": issue_key,
                                    "summary": issue_details.get("fields", {}).get("summary", ""),
                                    "status": issue_details.get("fields", {}).get("status", {}).get("name", "")
                                })
                        except Exception as e:
                            logger.error(f"Error getting Jira issue details: {str(e)}")
                    
        except Exception as e:
            logger.exception(f"Error processing message: {str(e)}")
            assistant_content = f"I'm sorry, but I encountered an error while processing your request."
            jira_references = []
            
        # Create the assistant message
        assistant_message = Message(
            content=assistant_content,
            role="assistant",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        conversation.messages.append(assistant_message)
        
        # Save the updated conversation
        self._conversations[conversation.id] = conversation
        
        # Return the response
        return {
            "message": assistant_message.content,
            "conversation_id": conversation.id,
            "jira_references": jira_references  # Contains Jira issue keys and summaries
        }
    
    async def process_message_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Process a user message and generate a streaming response
        
        Args:
            message: The user's message
            conversation_id: Optional ID of an existing conversation
            user_id: Optional user ID
            
        Yields:
            Chunks of the response as they become available
        """
        # Get or create conversation
        conversation = self._get_or_create_conversation(conversation_id, user_id)
        
        # Add user message to conversation
        timestamp = datetime.utcnow().isoformat() + "Z"
        user_message = Message(content=message, role="user", timestamp=timestamp)
        conversation.messages.append(user_message)
        
        # Update conversation timestamp
        conversation.updated_at = timestamp
        
        # Yield initial message to let the client know we're processing
        yield {
            "event": "start",
            "conversation_id": conversation.id,
            "message": "",
            "done": False
        }
        
        # Extract the messages for the LLM (excluding system messages)
        chat_messages = [{"role": msg.role, "content": msg.content} 
                       for msg in conversation.messages[-10:]]  # Only use last 10 messages
        
        # Add a system prompt for Jira context
        system_prompt = """You are a helpful AI assistant for Jira tasks. You can help with:
1. Creating new issues
2. Updating existing issues
3. Searching for issues
4. Adding comments to issues
5. Explaining Jira concepts

When asked to perform Jira operations, provide clear, accurate responses
with the relevant Jira issue keys and summaries."""

        full_response = ""
        jira_references = []

        try:
            # Use the streaming version of the LLM service
            async for chunk in self.llm_service.generate_chat_completion_stream(
                messages=chat_messages,
                model="anthropic/claude-3-sonnet",  # Use a capable model
                max_tokens=1000,
                system_prompt=system_prompt
            ):
                if "error" in chunk:
                    yield {
                        "event": "error",
                        "message": f"Error: {chunk['error']}",
                        "done": True
                    }
                    full_response = f"I'm sorry, but I encountered an error processing your request."
                    break
                
                # Extract content from the chunk
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if content:
                    full_response += content
                    yield {
                        "event": "token",
                        "message": content,
                        "done": False
                    }
        
            # After streaming is done, check for Jira references
            import re
            issue_matches = re.findall(r'([A-Z]+-\d+)', full_response)
            if issue_matches:
                # Get issue details from Jira
                for issue_key in issue_matches:
                    try:
                        issue_details = await self.mcp_service.call_tool(
                            "jira_get_issue",
                            {"issue_key": issue_key}
                        )
                        if "error" not in issue_details:
                            jira_reference = {
                                "key": issue_key,
                                "summary": issue_details.get("fields", {}).get("summary", ""),
                                "status": issue_details.get("fields", {}).get("status", {}).get("name", "")
                            }
                            jira_references.append(jira_reference)
                            yield {
                                "event": "reference",
                                "reference": jira_reference,
                                "done": False
                            }
                    except Exception as e:
                        pass  # Silently continue if we can't get issue details
                
        except Exception as e:
            yield {
                "event": "error",
                "message": f"Error: {str(e)}",
                "done": True
            }
            full_response = f"I'm sorry, but I encountered an error processing your request."
        
        # Create the assistant message and add it to the conversation
        assistant_message = Message(
            content=full_response,
            role="assistant",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        conversation.messages.append(assistant_message)
        
        # Save the updated conversation
        self._conversations[conversation.id] = conversation
        
        # Send final message
        yield {
            "event": "end",
            "conversation_id": conversation.id,
            "message": full_response,
            "jira_references": jira_references,
            "done": True
        }
    
    def _get_or_create_conversation(
        self,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Conversation:
        """
        Get an existing conversation or create a new one
        
        Args:
            conversation_id: Optional ID of an existing conversation
            user_id: Optional user ID
            
        Returns:
            The conversation object
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]
            
        # Create a new conversation
        conversation_id = f"conv_{uuid4().hex}"
        
        # Initial system message
        system_message = Message(
            content="How can I help you with your Jira tasks today?",
            role="assistant",
            timestamp=timestamp
        )
        
        conversation = Conversation(
            id=conversation_id,
            messages=[system_message],
            user_id=user_id,
            created_at=timestamp,
            updated_at=timestamp
        )
        
        self._conversations[conversation_id] = conversation
        return conversation
