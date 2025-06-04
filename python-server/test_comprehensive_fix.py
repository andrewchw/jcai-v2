import re
import sys

sys.path.append(".")


def test_entity_patterns():
    """Test the updated entity patterns"""

    # Import the patterns from the service
    from app.services.dialogflow_llm_service import ENTITY_PATTERNS

    user_input = 'Summary : "Test summary creation", Assignee : "Anson Chan", Due Date : "Friday" for Create Issue'
    print(f"Testing input: {user_input}")
    print("=" * 60)

    # Test each pattern
    extracted_entities = {}

    for entity_type, pattern in ENTITY_PATTERNS.items():
        matches = re.findall(pattern, user_input, re.IGNORECASE)
        if matches:
            print(f"{entity_type} pattern: {pattern}")
            print(f"  Raw matches: {matches}")

            # Apply the same extraction logic as the service
            if entity_type == "project_key":
                # Handle project key special case
                for match in (
                    matches[0] if isinstance(matches[0], tuple) else [matches[0]]
                ):
                    if match and re.match(r"^[A-Z]{2,10}$", match):
                        extracted_entities[entity_type] = match
                        print(f"  Extracted value: {match}")
                        break
            elif entity_type in ["assignee", "summary", "due_date", "priority"]:
                # Handle patterns with optional quoted/unquoted formats
                if isinstance(matches[0], tuple):
                    # Find the first non-empty group
                    value = next(
                        (group for group in matches[0] if group and group.strip()), None
                    )
                    if value:
                        extracted_entities[entity_type] = value.strip()
                        print(f"  Extracted value: '{value.strip()}'")
                else:
                    extracted_entities[entity_type] = matches[0].strip()
                    print(f"  Extracted value: '{matches[0].strip()}'")
            else:
                # Simple single-group patterns
                value = (
                    matches[0] if not isinstance(matches[0], tuple) else matches[0][0]
                )
                extracted_entities[entity_type] = value
                print(f"  Extracted value: '{value}'")
            print()

    print("Final extracted entities:")
    for entity_type, value in extracted_entities.items():
        print(f"  {entity_type}: '{value}'")

    return extracted_entities


def test_due_date_processing():
    """Test due date processing logic"""
    from datetime import datetime, timedelta

    print("\n" + "=" * 60)
    print("Testing due date processing:")

    test_dates = ["Friday", "today", "tomorrow", "next week", "2025-06-01"]

    for due_date_str in test_dates:
        print(f"\nProcessing due date: '{due_date_str}'")

        due_date_str_lower = due_date_str.lower().strip()

        # Handle relative dates (same logic as in create_issue_action)
        if due_date_str_lower in ["today"]:
            due_date = datetime.now().strftime("%Y-%m-%d")
        elif due_date_str_lower in ["tomorrow"]:
            due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif due_date_str_lower in [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]:
            # Calculate next occurrence of the specified day
            days_of_week = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4,
                "saturday": 5,
                "sunday": 6,
            }
            target_day = days_of_week[due_date_str_lower]
            current_day = datetime.now().weekday()
            days_ahead = target_day - current_day
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            due_date = (datetime.now() + timedelta(days=days_ahead)).strftime(
                "%Y-%m-%d"
            )
        elif due_date_str_lower == "next week":
            due_date = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
        elif due_date_str_lower == "next month":
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            # Assume it's already in YYYY-MM-DD format or try to parse it            try:
            parsed_date = datetime.strptime(due_date_str_lower, "%Y-%m-%d")
            due_date = due_date_str_lower

        if due_date:
            print(f"  -> Converted to: {due_date}")
        else:
            print("  -> Could not parse date")


if __name__ == "__main__":
    # Test entity extraction
    entities = test_entity_patterns()

    # Test due date processing
    test_due_date_processing()

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"✅ Summary extracted: {'summary' in entities}")
    print(f"✅ Assignee extracted: {'assignee' in entities}")
    print(f"✅ Due date extracted: {'due_date' in entities}")

    if all(key in entities for key in ["summary", "assignee", "due_date"]):
        print("\n🎉 All entities successfully extracted!")
        print("The original issue should now be resolved.")
    else:
        print("\n❌ Some entities are still missing.")
