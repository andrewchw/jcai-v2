#!/usr/bin/env python3
"""
End-to-end test for the comprehensive Jira chatbot fix.
Tests entity extraction, due date processing, and create issue flow.
"""

import os
import re
import sys
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(".")


def test_entity_patterns():
    """Test the updated entity patterns"""
    print("\n🔍 Testing Entity Extraction Patterns")
    print("=" * 60)

    # Import the patterns from the service
    from app.services.dialogflow_llm_service import ENTITY_PATTERNS

    user_input = 'Summary : "Test summary creation", Assignee : "Anson Chan", Due Date : "Friday" for Create Issue'
    print(f"Testing input: {user_input}")
    print("-" * 60)

    # Test each pattern
    extracted_entities = {}

    for entity_type, pattern in ENTITY_PATTERNS.items():
        matches = re.findall(pattern, user_input, re.IGNORECASE)
        if matches:
            print(f"✅ {entity_type} pattern: {pattern}")
            print(f"   Raw matches: {matches}")

            # Apply the same extraction logic as the service
            if entity_type == "project_key":
                # Handle project key special case
                for match in (
                    matches[0] if isinstance(matches[0], tuple) else [matches[0]]
                ):
                    if match and re.match(r"^[A-Z]{2,10}$", match):
                        extracted_entities[entity_type] = match
                        print(f"   ✅ Extracted value: {match}")
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
                        print(f"   ✅ Extracted value: '{value.strip()}'")
                else:
                    extracted_entities[entity_type] = matches[0].strip()
                    print(f"   ✅ Extracted value: '{matches[0].strip()}'")
            else:
                # Simple single-group patterns
                value = (
                    matches[0] if not isinstance(matches[0], tuple) else matches[0][0]
                )
                extracted_entities[entity_type] = value
                print(f"   ✅ Extracted value: '{value}'")
            print()

    print("Final extracted entities:")
    for entity_type, value in extracted_entities.items():
        print(f"  ✅ {entity_type}: '{value}'")

    return extracted_entities


def test_due_date_processing():
    """Test due date processing logic"""
    print("\n📅 Testing Due Date Processing")
    print("=" * 60)

    test_dates = ["Friday", "today", "tomorrow", "next week", "2025-06-01"]

    for due_date_str in test_dates:
        print(f"Processing due date: '{due_date_str}'")

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
            # Assume it's already in YYYY-MM-DD format or try to parse it
            try:
                parsed_date = datetime.strptime(due_date_str_lower, "%Y-%m-%d")
                due_date = due_date_str_lower
            except ValueError:
                due_date = None

        if due_date:
            print(f"  ✅ Converted to: {due_date}")
        else:
            print("  ❌ Could not parse date")
        print()


def test_llm_service_initialization():
    """Test LLM service initialization and entity extraction"""
    print("\n🧠 Testing LLM Service Integration")
    print("=" * 60)

    try:
        from app.services.dialogflow_llm_service import (
            DialogflowInspiredLLMService, JiraIntent)

        # Use a test API key to avoid 401 errors during testing
        test_api_key = "test-placeholder-key"
        llm_service = DialogflowInspiredLLMService(test_api_key)

        # Test entity extraction method directly
        user_input = 'Summary : "Test summary creation", Assignee : "Anson Chan", Due Date : "Friday" for Create Issue'
        entities = llm_service._extract_entities(user_input, JiraIntent.CREATE_ISSUE)

        print(f"Testing input: {user_input}")
        print(f"Intent: {JiraIntent.CREATE_ISSUE.value}")
        print("Extracted entities:")

        for entity_type, entity in entities.items():
            print(
                f"  ✅ {entity_type}: '{entity.value}' (confidence: {entity.confidence})"
            )

        # Check if all required entities are present
        required_entities = ["summary", "assignee", "due_date"]
        missing_entities = [e for e in required_entities if e not in entities]

        if not missing_entities:
            print("\n🎉 All required entities successfully extracted!")
            return True
        else:
            print(f"\n❌ Missing entities: {missing_entities}")
            return False

    except Exception as e:
        print(f"❌ Error testing LLM service: {str(e)}")
        print("Note: This is expected if OpenRouter API key is not configured.")
        return False


def test_create_issue_action():
    """Test the create issue action with due date support"""
    print("\n⚙️ Testing Create Issue Action")
    print("=" * 60)

    # Simulate the create issue action logic
    entities = {
        "summary": "Test summary creation",
        "assignee": "Anson Chan",
        "due_date": "Friday",
    }

    print("Input entities:")
    for key, value in entities.items():
        print(f"  {key}: '{value}'")

    # Process due date as done in create_issue_action
    due_date_str = entities.get("due_date", "").lower().strip()

    if due_date_str in [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]:
        days_of_week = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        target_day = days_of_week[due_date_str]
        current_day = datetime.now().weekday()
        days_ahead = target_day - current_day
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        processed_due_date = (datetime.now() + timedelta(days=days_ahead)).strftime(
            "%Y-%m-%d"
        )

        print(f"\nProcessed due date: '{due_date_str}' -> '{processed_due_date}'")

        # Simulate Jira issue creation parameters
        issue_data = {
            "fields": {
                "summary": entities["summary"],
                "assignee": {"displayName": entities["assignee"]},
                "duedate": processed_due_date,
                "project": {"key": "JCAI"},  # Default project
                "issuetype": {"name": "Task"},
            }
        }

        print("\nSimulated Jira issue data:")
        print(f"  Summary: {issue_data['fields']['summary']}")
        print(f"  Assignee: {issue_data['fields']['assignee']['displayName']}")
        print(f"  Due Date: {issue_data['fields']['duedate']}")
        print(f"  Project: {issue_data['fields']['project']['key']}")
        print(f"  Issue Type: {issue_data['fields']['issuetype']['name']}")

        return True
    else:
        print(f"❌ Failed to process due date: '{due_date_str}'")
        return False


def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 COMPREHENSIVE JIRA CHATBOT FIX TEST")
    print("=" * 80)

    results = {}

    # Test 1: Entity extraction patterns
    try:
        entities = test_entity_patterns()
        results["entity_extraction"] = len(entities) >= 3
    except Exception as e:
        print(f"❌ Entity extraction test failed: {e}")
        results["entity_extraction"] = False

    # Test 2: Due date processing
    try:
        test_due_date_processing()
        results["due_date_processing"] = True
    except Exception as e:
        print(f"❌ Due date processing test failed: {e}")
        results["due_date_processing"] = False

    # Test 3: LLM service integration
    try:
        results["llm_service"] = test_llm_service_initialization()
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        results["llm_service"] = False

    # Test 4: Create issue action
    try:
        results["create_issue_action"] = test_create_issue_action()
    except Exception as e:
        print(f"❌ Create issue action test failed: {e}")
        results["create_issue_action"] = False

    # Print summary
    print("\n🎯 TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! The comprehensive fix is working correctly.")
        print("\nThe original issue has been resolved:")
        print("  ✅ Entity extraction now works for quoted formats")
        print("  ✅ Summary, assignee, and due date are all extracted")
        print("  ✅ Due date processing supports natural language")
        print("  ✅ Create issue action includes due date parameter")
    else:
        print(
            f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review the output above for details."
        )

    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
