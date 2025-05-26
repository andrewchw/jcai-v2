# Dialogflow-Inspired Architecture for Jira Chatbot

## Intent-Based Processing Pipeline

### 1. Intent Classification
```python
JIRA_INTENTS = {
    "create_issue": {
        "patterns": ["create", "add", "new", "make"],
        "entities": ["summary", "project", "assignee", "due_date", "priority"],
        "response_template": "Created {project}-{issue_number}: {summary}"
    },
    "query_issues": {
        "patterns": ["show", "list", "find", "search", "get"],
        "entities": ["assignee", "project", "status", "due_date"],
        "response_template": "Found {count} issues matching your criteria"
    },
    "update_issue": {
        "patterns": ["update", "change", "modify", "edit"],
        "entities": ["issue_key", "field", "value"],
        "response_template": "Updated {issue_key}: {field} → {value}"
    },
    "assign_issue": {
        "patterns": ["assign", "give to", "allocate"],
        "entities": ["issue_key", "assignee"],
        "response_template": "Assigned {issue_key} to {assignee}"
    },
    "transition_issue": {
        "patterns": ["complete", "close", "done", "finish", "start", "in progress"],
        "entities": ["issue_key", "status"],
        "response_template": "Moved {issue_key} to {status}"
    }
}
```

### 2. Entity Extraction Patterns
```python
JIRA_ENTITIES = {
    "issue_key": r"[A-Z]+-\d+",
    "username": r"@(\w+)",
    "project_key": r"[A-Z]{2,10}",
    "due_date": ["today", "tomorrow", "friday", "next week", r"\d{4}-\d{2}-\d{2}"],
    "priority": ["low", "medium", "high", "critical", "urgent"]
}
```

### 3. Context Management
```python
class ConversationContext:
    def __init__(self):
        self.current_intent = None
        self.missing_entities = []
        self.session_data = {}

    def set_context(self, intent, entities):
        self.current_intent = intent
        self.missing_entities = self.get_missing_required_entities(intent, entities)

    def needs_clarification(self):
        return len(self.missing_entities) > 0
```

## Implementation Strategy

### Phase 1: Core Intent Processing (Days 13-15)
1. **Intent Classifier**: Use LLM to classify user input into predefined Jira intents
2. **Entity Extractor**: Extract structured data from natural language
3. **Response Generator**: Template-based responses for consistency

### Phase 2: Context & Conversation Flow (Days 16-18)
1. **Multi-turn Support**: Handle incomplete requests with follow-up questions
2. **Session Memory**: Remember user preferences and current context
3. **Confirmation Patterns**: "Are you sure you want to delete issue PROJ-123?"

### Phase 3: Advanced Features (Days 19-21)
1. **Small Talk**: Handle greetings and non-Jira queries gracefully
2. **Learning**: Improve intent recognition based on user feedback
3. **Shortcuts**: Learn user patterns and suggest shortcuts
