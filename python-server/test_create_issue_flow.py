import asyncio
import json
import sys

sys.path.append(".")


async def test_create_issue():
    import os

    from app.api.endpoints.chat import process_chat_message
    from app.core.config import settings
    from app.services.dialogflow_llm_service import \
        DialogflowInspiredLLMService
    from app.services.multi_user_jira_service import MultiUserJiraService

    # Mock user ID
    user_id = "test_user"

    # Test the exact user input
    user_input = 'Summary : "Test summary creation", Assignee : "Anson Chan", Due Date : "Friday" for Create Issue'

    print(f"Testing chat message: {user_input}")

    try:
        # Initialize services (mock API key for testing)
        os.environ["OPENROUTER_API_KEY"] = "test-key"

        # Test just the entity extraction part
        service = DialogflowInspiredLLMService("test-key")

        # Mock conversation context
        from app.services.dialogflow_llm_service import (ConversationContext,
                                                         JiraIntent)

        context = ConversationContext(user_id)

        # Test intent classification
        intent = service._classify_intent(user_input, context)
        print(f"Classified intent: {intent}")

        # Test entity extraction
        entities = service._extract_entities(user_input, intent)
        print("Extracted entities:")
        for entity_type, entity in entities.items():
            print(f"  {entity_type}: {entity.value}")

        # Test if all required entities are present
        required_entities = service._get_required_entities(intent)
        missing_entities = service._find_missing_entities(entities, required_entities)
        print(f"Required entities: {required_entities}")
        print(f"Missing entities: {missing_entities}")

        # Test action generation
        context.current_intent = intent
        context.entities = entities
        action = service._get_jira_action(context)
        print(f"Generated action: {json.dumps(action, indent=2)}")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_create_issue())
