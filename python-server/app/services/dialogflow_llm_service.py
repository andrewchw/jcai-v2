"""
Dialogflow-inspired LLM service for Jira Chatbot.

This module implements intent-based natural language processing
following Dialogflow architectural patterns but using OpenRouter LLM.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

logger = logging.getLogger(__name__)


class JiraIntent(Enum):
    CREATE_ISSUE = "create_issue"
    QUERY_ISSUES = "query_issues"
    UPDATE_ISSUE = "update_issue"
    ASSIGN_ISSUE = "assign_issue"
    TRANSITION_ISSUE = "transition_issue"
    ADD_COMMENT = "add_comment"
    UPLOAD_ATTACHMENT = "upload_attachment"
    SMALL_TALK = "small_talk"
    HELP = "help"
    UNKNOWN = "unknown"


class JiraEntity:
    """Extracted entity from user input"""

    def __init__(self, entity_type: str, value: str, confidence: float = 1.0):
        self.entity_type = entity_type
        self.value = value
        self.confidence = confidence


class ConversationContext:
    """Manages conversation state and context"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_intent: Optional[JiraIntent] = None
        self.entities: Dict[str, JiraEntity] = {}
        self.missing_entities: List[str] = []
        self.session_data: Dict[str, Any] = {}
        self.conversation_history: List[Dict] = []

        # Search pagination state
        self.last_search_results: List[
            Dict
        ] = (
            []
        )  # Store complete search results        self.last_search_params: Dict[str, Any] = {}  # Store search parameters
        self.search_display_index: int = 0  # Track how many issues have been shown
        self.search_page_size: int = 8  # How many issues to show per page

    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )
        # Keep only last 10 messages to avoid memory bloat
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def set_intent(self, intent: JiraIntent, entities: Dict[str, JiraEntity]):
        self.current_intent = intent
        self.entities.update(entities)
        self.missing_entities = self._get_missing_required_entities()

    def _get_missing_required_entities(self) -> List[str]:
        """Get list of missing required entities for the current intent"""
        if not self.current_intent:
            return []

        required_entities = INTENT_REQUIREMENTS.get(self.current_intent, [])
        missing = []

        for required_entity in required_entities:
            if required_entity not in self.entities:
                missing.append(required_entity)

        return missing

    def store_search_results(self, results: List[Dict], search_params: Dict[str, Any]):
        """Store search results for pagination"""
        self.last_search_results = results
        self.last_search_params = search_params
        self.search_display_index = 0  # Reset display index for new search

    def get_next_search_page(self) -> Tuple[List[Dict], bool]:
        """Get the next page of search results"""
        start_index = self.search_display_index
        end_index = start_index + self.search_page_size

        page_results = self.last_search_results[start_index:end_index]
        has_more = end_index < len(self.last_search_results)

        # Update display index for next call
        self.search_display_index = end_index

        return page_results, has_more

    def is_pagination_request(self, message: str) -> bool:
        """Check if the message is asking for more results from previous search"""
        pagination_keywords = [
            "show more",
            "more issues",
            "show more issues",
            "next",
            "continue",
            "more results",
            "show remaining",
            "show rest",
            "see more",
        ]
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in pagination_keywords)

    def has_more_search_results(self) -> bool:
        """Check if there are more search results to show"""
        return self.search_display_index < len(self.last_search_results)

    def clear_search_state(self):
        """Clear search results and pagination state"""
        self.last_search_results = []
        self.last_search_params = {}
        self.search_display_index = 0


# Intent configuration following Dialogflow pattern
INTENT_REQUIREMENTS = {
    JiraIntent.CREATE_ISSUE: ["summary"],
    JiraIntent.ASSIGN_ISSUE: ["issue_key", "assignee"],
    JiraIntent.UPDATE_ISSUE: ["issue_key", "field", "value"],
    JiraIntent.TRANSITION_ISSUE: ["issue_key", "status"],
    JiraIntent.ADD_COMMENT: ["issue_key", "comment"],
}

ENTITY_PATTERNS = {
    "issue_key": r"([A-Z]+-\d+)",
    "username": r"@(\w+)",
    "project_key": r"\b(project\s+([A-Z]{2,10})|in\s+([A-Z]{2,10})|([A-Z]{2,10})\s+project)\b",
    "due_date": r"(\d{4}-\d{2}-\d{2}|today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next week|next month)",
    "priority": r"(low|medium|high|critical|urgent|blocker)",
    "status": r"(todo|to do|in progress|done|completed|closed|open|resolved)",
}

INTENT_PATTERNS = {
    JiraIntent.CREATE_ISSUE: ["create", "add", "new", "make", "build"],
    JiraIntent.QUERY_ISSUES: ["show", "list", "find", "search", "get", "what", "which"],
    JiraIntent.UPDATE_ISSUE: ["update", "change", "modify", "edit", "set"],
    JiraIntent.ASSIGN_ISSUE: ["assign", "give to", "allocate", "delegate"],
    JiraIntent.TRANSITION_ISSUE: [
        "complete",
        "close",
        "done",
        "finish",
        "start",
        "in progress",
        "move to",
    ],
    JiraIntent.ADD_COMMENT: ["comment", "note", "add note", "mention"],
    JiraIntent.SMALL_TALK: ["hello", "hi", "thanks", "thank you", "how are you"],
    JiraIntent.HELP: ["help", "what can you do", "commands", "usage"],
}


class DialogflowInspiredLLMService:
    """LLM service implementing Dialogflow-style intent processing"""

    def __init__(
        self, openrouter_api_key: str, model: str = "meta-llama/llama-3-8b-instruct"
    ):
        self.api_key = openrouter_api_key
        self.model = model
        self.contexts: Dict[str, ConversationContext] = {}

        # Initialize OpenRouter client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )

    async def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Main processing pipeline following Dialogflow pattern"""

        # Get or create conversation context
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id)

        context = self.contexts[user_id]
        context.add_message("user", message)

        # Step 1: Intent Classification
        intent = self._classify_intent(message, context)

        # Step 2: Entity Extraction
        entities = self._extract_entities(message, intent)

        # Step 3: Update Context
        context.set_intent(intent, entities)

        # Step 4: Generate Response
        if context.missing_entities:
            response = self._generate_clarification_question(context)
            response_type = "clarification"
        else:
            response = await self.generate_enhanced_fulfillment_response(context)
            response_type = "fulfillment"

        context.add_message("assistant", response["text"])

        return {
            "intent": intent.value,
            "entities": {k: v.value for k, v in entities.items()},
            "response": response,
            "response_type": response_type,
            "confidence": response.get("confidence", 0.8),
            "context": {
                "missing_entities": context.missing_entities,
                "session_data": context.session_data,
            },
        }

    def _classify_intent(
        self, message: str, context: ConversationContext
    ) -> JiraIntent:
        """Classify user intent using pattern matching + LLM"""

        message_lower = message.lower()

        # Check for pagination requests first
        if context.is_pagination_request(message) and context.has_more_search_results():
            return JiraIntent.QUERY_ISSUES

        # Quick pattern-based classification first
        for intent, patterns in INTENT_PATTERNS.items():
            if any(pattern in message_lower for pattern in patterns):
                return intent

        # If context suggests continuation of previous intent
        if context.current_intent and context.missing_entities:
            return context.current_intent
            # Fall back to LLM classification for complex cases
        return self._llm_classify_intent(message, context)

    def _extract_entities(
        self, message: str, intent: JiraIntent
    ) -> Dict[str, JiraEntity]:
        """Extract entities using regex patterns + LLM"""

        entities = {}

        # Only extract entities for intents that need them
        if intent in [JiraIntent.SMALL_TALK, JiraIntent.HELP]:
            return entities

        # Pattern-based extraction
        for entity_type, pattern in ENTITY_PATTERNS.items():
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                # Handle project_key pattern which has multiple groups
                if entity_type == "project_key":
                    # Extract the actual project key from the matched groups
                    for match in (
                        matches[0] if isinstance(matches[0], tuple) else [matches[0]]
                    ):
                        if match and re.match(r"^[A-Z]{2,10}$", match):
                            entities[entity_type] = JiraEntity(entity_type, match)
                            break
                else:
                    entities[entity_type] = JiraEntity(entity_type, matches[0])

        # LLM-based extraction for complex entities
        if intent in [JiraIntent.CREATE_ISSUE, JiraIntent.ADD_COMMENT]:
            summary = self._extract_summary_with_llm(message)
            if summary:
                entities["summary"] = JiraEntity("summary", summary)

        return entities

    def _generate_clarification_question(
        self, context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate follow-up questions for missing entities"""

        missing = context.missing_entities[0]  # Ask for one at a time

        clarification_templates = {
            "summary": "What should be the summary/title for this issue?",
            "assignee": "Who should this be assigned to?",
            "project": "Which project should this be created in?",
            "issue_key": "Which issue are you referring to? (e.g., PROJ-123)",
            "priority": "What priority should this have? (low/medium/high/critical)",
            "due_date": "When is this due? (e.g., today, Friday, 2025-06-01)",
        }

        return {
            "text": clarification_templates.get(
                missing, f"Please provide the {missing}."
            ),
            "type": "clarification",
            "missing_entity": missing,
        }

    def _generate_fulfillment_response(
        self, context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate response when all entities are available"""

        templates = {
            JiraIntent.CREATE_ISSUE: "I'll create a new issue: '{summary}' in project {project}.",
            JiraIntent.ASSIGN_ISSUE: "I'll assign {issue_key} to {assignee}.",
            JiraIntent.TRANSITION_ISSUE: "I'll move {issue_key} to {status}.",
            JiraIntent.QUERY_ISSUES: "Let me search for issues matching your criteria...",
            JiraIntent.SMALL_TALK: "Hello! I'm here to help you manage your Jira tasks. What would you like to do?",
            JiraIntent.HELP: "I can help you create issues, assign tasks, update status, search for issues, and add comments. What would you like to do?",
        }

        template = templates.get(context.current_intent, "I'll help you with that.")

        # Replace entity placeholders
        for entity_type, entity in context.entities.items():
            template = template.replace(f"{{{entity_type}}}", entity.value)

        return {
            "text": template,
            "type": "fulfillment",
            "action": self._get_jira_action(context),
            "confidence": 0.9,
        }

    async def generate_enhanced_fulfillment_response(
        self, context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate enhanced response using LLM"""
        base_response = self._generate_fulfillment_response(context)

        if context.current_intent not in [JiraIntent.SMALL_TALK, JiraIntent.HELP]:
            enhanced_text = await self._llm_enhance_response(
                context, base_response["text"]
            )
            base_response["text"] = enhanced_text

        return base_response

    def _get_jira_action(self, context: ConversationContext) -> Dict[str, Any]:
        """Convert intent + entities to Jira API action"""

        action_map = {
            JiraIntent.CREATE_ISSUE: "create_issue",
            JiraIntent.ASSIGN_ISSUE: "assign_issue",
            JiraIntent.TRANSITION_ISSUE: "transition_issue",
            JiraIntent.QUERY_ISSUES: "search_issues",
            JiraIntent.ADD_COMMENT: "add_comment",
        }

        action = action_map.get(context.current_intent)
        if not action:
            return {}

        # Convert entities to API parameters
        params = {}
        for entity_type, entity in context.entities.items():
            params[entity_type] = entity.value

        return {"type": action, "parameters": params}

    def _llm_classify_intent(
        self, message: str, context: ConversationContext
    ) -> JiraIntent:
        """Use LLM for complex intent classification"""

        # Build prompt for intent classification
        available_intents = [intent.value for intent in JiraIntent]

        prompt = f"""You are a Jira assistant that classifies user intents.
Given the user message, classify it into one of these intents:
{', '.join(available_intents)}

Recent conversation context:
{json.dumps(context.conversation_history[-3:], indent=2) if context.conversation_history else 'No prior context'}

User message: "{message}"

Respond with only the intent name (e.g., "create_issue", "query_issues", etc.).
If unsure, respond with "unknown"."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3,
            )

            predicted_intent = response.choices[0].message.content.strip().lower()

            # Validate the prediction
            for intent in JiraIntent:
                if intent.value == predicted_intent:
                    logger.info(f"LLM classified intent: {predicted_intent}")
                    return intent

            logger.warning(f"LLM returned invalid intent: {predicted_intent}")
            return JiraIntent.UNKNOWN

        except Exception as e:
            logger.error(f"LLM intent classification failed: {e}")
            return JiraIntent.UNKNOWN

    def _extract_summary_with_llm(self, message: str) -> Optional[str]:
        """Use LLM to extract issue summary from natural language"""

        prompt = f"""Extract a clear, concise issue summary from this user message.
The summary should be suitable as a Jira issue title (under 100 characters).

User message: "{message}"

Extract only the core issue/task description. Do not include action words like "create", "make", "add".
If no clear summary can be extracted, respond with "NONE".

Examples:
"Create a bug report for login issues" -> "Login issues"
"I need to add a new feature for user profiles" -> "User profiles feature"
"Make a task to update the documentation" -> "Update documentation"

Summary:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3,
            )

            summary = response.choices[0].message.content.strip()

            if summary.upper() == "NONE" or len(summary) > 100:
                return None

            logger.info(f"LLM extracted summary: {summary}")
            return summary

        except Exception as e:
            logger.error(f"LLM summary extraction failed: {e}")
            return None

    async def _llm_enhance_response(
        self, context: ConversationContext, base_response: str
    ) -> str:
        """Use LLM to enhance response with natural language"""

        prompt = f"""You are a helpful Jira assistant. Enhance this response to be more natural and conversational while keeping it concise.

Current context:
- Intent: {context.current_intent.value if context.current_intent else 'unknown'}
- Entities: {json.dumps({k: v.value for k, v in context.entities.items()}, indent=2)}

Base response: "{base_response}"

Make the response:
1. Friendly and professional
2. Confirm what action will be taken
3. Include relevant details from entities
4. Keep it under 2 sentences

Enhanced response:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
            )

            enhanced = response.choices[0].message.content.strip()
            logger.info(f"LLM enhanced response: {enhanced}")
            return enhanced

        except Exception as e:
            logger.error(f"LLM response enhancement failed: {e}")
            return base_response

    def get_conversation_context(self, user_id: str) -> ConversationContext:
        """Get the conversation context for a user"""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id)
        return self.contexts[user_id]
