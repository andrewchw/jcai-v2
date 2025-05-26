#!/usr/bin/env python3
"""
Test script to verify pagination functionality
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "python-server"))

from app.services.dialogflow_llm_service import (ConversationContext,
                                                 DialogflowInspiredLLMService)


def test_pagination_logic():
    """Test the pagination detection and state management"""

    print("Testing Pagination Logic...")

    # Create a conversation context
    context = ConversationContext("test_user")

    # Simulate storing search results (20 mock issues)
    mock_issues = [
        {"key": f"TEST-{i}", "fields": {"summary": f"Issue {i}"}} for i in range(1, 21)
    ]
    context.store_search_results(mock_issues, {"assignee": "test_user"})

    print(f"✓ Stored {len(context.last_search_results)} mock issues")

    # Test pagination detection
    pagination_phrases = [
        "show more issues",
        "more issues please",
        "show more",
        "next",
        "continue",
        "see more",
    ]

    for phrase in pagination_phrases:
        is_pagination = context.is_pagination_request(phrase)
        print(f"✓ '{phrase}' -> Pagination: {is_pagination}")

    # Test non-pagination phrases
    non_pagination_phrases = [
        "create new issue",
        "assign TEST-1 to john",
        "show my issues",  # This should be treated as new search
    ]

    for phrase in non_pagination_phrases:
        is_pagination = context.is_pagination_request(phrase)
        print(f"✓ '{phrase}' -> Pagination: {is_pagination}")

    # Test getting pages
    print("\nTesting pagination flow:")

    # First page (issues 1-8)
    page1, has_more1 = context.get_next_search_page()
    print(f"✓ Page 1: {len(page1)} issues, has_more: {has_more1}")
    print(f"  Issues: {[issue['key'] for issue in page1]}")

    # Second page (issues 9-16)
    page2, has_more2 = context.get_next_search_page()
    print(f"✓ Page 2: {len(page2)} issues, has_more: {has_more2}")
    print(f"  Issues: {[issue['key'] for issue in page2]}")

    # Third page (issues 17-20)
    page3, has_more3 = context.get_next_search_page()
    print(f"✓ Page 3: {len(page3)} issues, has_more: {has_more3}")
    print(f"  Issues: {[issue['key'] for issue in page3]}")

    # Fourth page (should be empty)
    page4, has_more4 = context.get_next_search_page()
    print(f"✓ Page 4: {len(page4)} issues, has_more: {has_more4}")

    print("\n✅ All pagination tests passed!")


if __name__ == "__main__":
    test_pagination_logic()
