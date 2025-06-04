import re
import sys

sys.path.append(".")

# Test entity extraction with user's exact input
user_input = 'Summary : "Test summary creation", Assignee : "Anson Chan", Due Date : "Friday" for Create Issue'
print(f"Testing input: {user_input}")

# Read and test updated patterns
patterns = {
    "summary": r"summary\s*[:=]\s*[\"\'](.*?)[\"\']\s*|summary\s*[:=]\s*([^,\n]+?)(?:\s*,|\s*$|\s*for|\s*and)",
    "assignee": r"assignee\s*[:=]\s*[\"\'](.*?)[\"\']\s*|assignee\s*[:=]\s*([^,\n]+?)(?:\s*,|\s*$|\s*for|\s*and)",
    "due_date": r"due\s*date\s*[:=]\s*[\"\'](.*?)[\"\']\s*|due\s*date\s*[:=]\s*([^,\n]+?)(?:\s*,|\s*$|\s*for|\s*and)|(\d{4}-\d{2}-\d{2}|today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next week|next month)",
    "priority": r"priority\s*[:=]\s*[\"\'](.*?)[\"\']\s*|priority\s*[:=]\s*([^,\n]+?)(?:\s*,|\s*$|\s*for|\s*and)|(low|medium|high|critical|urgent|blocker)",
}

print("\nTesting updated patterns:")
for name, pattern in patterns.items():
    matches = re.findall(pattern, user_input, re.IGNORECASE)
    print(f"{name} pattern matches: {matches}")

    # Test extraction logic (similar to what the service does)
    if matches:
        if isinstance(matches[0], tuple):
            # Find the first non-empty group
            value = next(
                (group for group in matches[0] if group and group.strip()), None
            )
            if value:
                print(f'  -> Extracted value: "{value.strip()}"')
        else:
            print(f'  -> Extracted value: "{matches[0].strip()}"')

# Test some other formats too
test_inputs = [
    'create issue with summary="My task" assignee="John Doe" due_date="tomorrow"',
    "Summary: Bug fix, Assignee: Alice, Due Date: next Friday",
    'Create task Summary: "Important feature" for project ABC',
]

print("\n" + "=" * 60)
print("Testing other input formats:")
for test_input in test_inputs:
    print(f"\nInput: {test_input}")
    for name, pattern in patterns.items():
        matches = re.findall(pattern, test_input, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                value = next(
                    (group for group in matches[0] if group and group.strip()), None
                )
                if value:
                    print(f'  {name}: "{value.strip()}"')
            else:
                print(f'  {name}: "{matches[0].strip()}"')
