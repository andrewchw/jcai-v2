import sys

sys.path.append(".")

try:
    from app.core.config import settings

    print("Settings loaded successfully")
    print(
        f'OPENROUTER_API_KEY: {"present" if settings.OPENROUTER_API_KEY else "missing"}'
    )

    from app.services.dialogflow_llm_service import \
        DialogflowInspiredLLMService

    print("Service imported successfully")

    service = DialogflowInspiredLLMService(
        settings.OPENROUTER_API_KEY, settings.DEFAULT_LLM_MODEL
    )
    print("Service initialized successfully")

    # Test a simple message
    from app.services.dialogflow_llm_service import ConversationContext

    context = ConversationContext("test_user")

    print("Testing entity extraction...")
    test_message = 'Summary : "Test summary creation", Assignee : "Anson Chan", Due Date : "Friday" for Create Issue'
    intent = service._classify_intent(test_message, context)
    print(f"Intent classified: {intent}")

    entities = service._extract_entities(test_message, intent)
    print(f"Entities extracted: {len(entities)} found")
    for entity_type, entity in entities.items():
        print(f"  {entity_type}: {entity.value}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
