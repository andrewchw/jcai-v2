"""
Test script for Dialogflow-inspired LLM service.

This script tests the intent classification and entity extraction
without requiring full API integration.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dialogflow_llm_service import (DialogflowInspiredLLMService,
                                                 JiraIntent)


def test_intent_classification():
    """Test intent classification with various user inputs"""

    service = DialogflowInspiredLLMService("test-key")

    test_cases = [
        ("Create a task for fixing the login bug", JiraIntent.CREATE_ISSUE),
        ("Show me all tasks assigned to John", JiraIntent.QUERY_ISSUES),
        ("Assign PROJ-123 to Sarah", JiraIntent.ASSIGN_ISSUE),
        ("Mark PROJ-456 as done", JiraIntent.TRANSITION_ISSUE),
        ("Add a comment to PROJ-789", JiraIntent.ADD_COMMENT),
        ("Hello there", JiraIntent.SMALL_TALK),
        ("What can you do?", JiraIntent.HELP),
    ]

    print("🎯 Testing Intent Classification")
    print("=" * 50)

    for text, expected_intent in test_cases:
        context = service.contexts.get("test_user")
        if not context:
            from app.services.dialogflow_llm_service import ConversationContext

            context = ConversationContext("test_user")
            service.contexts["test_user"] = context

        actual_intent = service._classify_intent(text, context)

        status = "✅" if actual_intent == expected_intent else "❌"
        print(
            f"{status} '{text}' → {actual_intent.value} (expected: {expected_intent.value})"
        )


def test_entity_extraction():
    """Test entity extraction from user inputs"""

    service = DialogflowInspiredLLMService("test-key")

    test_cases = [
        ("Assign PROJ-123 to @john due Friday", ["issue_key", "username", "due_date"]),
        ("Create a high priority task for fixing login", ["priority"]),
        ("Show tasks in JCAI project", ["project_key"]),
        ("Move TASK-456 to in progress", ["issue_key", "status"]),
    ]

    print("\n🔍 Testing Entity Extraction")
    print("=" * 50)

    for text, expected_entities in test_cases:
        entities = service._extract_entities(text, JiraIntent.CREATE_ISSUE)

        extracted_types = list(entities.keys())
        found_expected = [e for e in expected_entities if e in extracted_types]

        status = "✅" if len(found_expected) == len(expected_entities) else "⚠️"
        print(f"{status} '{text}'")

        for entity_type, entity in entities.items():
            print(f"    {entity_type}: '{entity.value}'")

        if len(found_expected) != len(expected_entities):
            missing = [e for e in expected_entities if e not in extracted_types]
            print(f"    Missing: {missing}")


def test_conversation_flow():
    """Test multi-turn conversation with missing entities"""

    service = DialogflowInspiredLLMService("test-key")
    user_id = "test_user"

    print("\n💬 Testing Conversation Flow")
    print("=" * 50)

    # First message - incomplete
    response1 = service.process_message(user_id, "Create a task")
    print(f"User: Create a task")
    print(f"Bot: {response1['response']['text']}")
    print(f"Type: {response1['response_type']}")

    # Second message - provide missing info
    response2 = service.process_message(user_id, "Fix the login bug")
    print(f"\nUser: Fix the login bug")
    print(f"Bot: {response2['response']['text']}")
    print(f"Type: {response2['response_type']}")

    # Third message - complete action
    if response2["response_type"] == "clarification":
        response3 = service.process_message(user_id, "JCAI")
        print(f"\nUser: JCAI")
        print(f"Bot: {response3['response']['text']}")
        print(f"Type: {response3['response_type']}")


def test_jira_action_generation():
    """Test Jira action parameter generation"""

    service = DialogflowInspiredLLMService("test-key")
    user_id = "test_user"

    print("\n⚙️ Testing Jira Action Generation")
    print("=" * 50)

    test_cases = [
        "Create a high priority task 'Fix login bug' assigned to @sarah",
        "Assign PROJ-123 to @john",
        "Move TASK-456 to done",
        "Show me all tasks assigned to @mike",
    ]

    for text in test_cases:
        response = service.process_message(user_id, text)
        print(f"Input: {text}")
        print(f"Intent: {response['intent']}")
        print(f"Entities: {response['entities']}")

        if "action" in response.get("response", {}):
            action = response["response"]["action"]
            print(f"Action: {action['type']}")
            print(f"Parameters: {action['parameters']}")
        print()


if __name__ == "__main__":
    print("🤖 Dialogflow-Inspired Jira Chatbot Test Suite")
    print("=" * 60)

    test_intent_classification()
    test_entity_extraction()
    test_conversation_flow()
    test_jira_action_generation()

    print("\n✨ Test Suite Complete!")
    print("\nNext Steps:")
    print("1. Run the Python server: cd python-server && python run.py")
    print("2. Test chat endpoint: POST /api/chat/message/test_user")
    print("3. Integrate with extension UI for real-time chat")
