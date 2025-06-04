# Jira Chatbot Command Guidelines

## Issue Creation Commands

The Jira chatbot supports various natural language formats for creating issues. Here are the recommended command formats:

### Basic Format
```
Summary: "Your issue title", Assignee: "Person Name", Due Date: "date" for Create Issue
```

### Supported Variations

#### Summary (Required)
- `Summary: "Bug in login feature"`
- `Summary = "New feature request"`
- `summary: Task completion`

#### Assignee (Optional)
- `Assignee: "John Doe"`
- `assignee = "Alice Smith"`
- `assign to "Bob Wilson"`
- `@username` (for username format)

#### Due Date (Optional)
- **Relative dates**: `Due Date: "today"`, `"tomorrow"`
- **Day names**: `"Monday"`, `"Friday"`, `"next Friday"`
- **Relative periods**: `"next week"`, `"next month"`
- **Specific dates**: `"2025-06-01"` (YYYY-MM-DD format)

#### Priority (Optional)
- `Priority: "high"`
- Values: `low`, `medium`, `high`, `critical`, `urgent`

### Example Commands

#### Complete Issue Creation
```
Summary: "Fix login bug", Assignee: "Alice Johnson", Due Date: "Friday", Priority: "high" for Create Issue
```

#### Minimal Issue Creation
```
Create issue with summary "Update documentation"
```

#### Various Formats
```
Summary = "Database optimization", Due Date = "next week" for new issue
```

```
Create task: Summary: "Code review", Assignee: "John", Priority: "medium"
```

```
New issue summary="Meeting notes", assignee="Sarah", due_date="tomorrow"
```

### Supported Intents

1. **Create Issue** - `create`, `add`, `new`, `make`, `build`
2. **Query Issues** - `show`, `list`, `find`, `search`, `get`, `what`, `which`
3. **Update Issue** - `update`, `change`, `modify`, `edit`, `set`
4. **Assign Issue** - `assign`, `give to`, `allocate`, `delegate`
5. **Transition Issue** - `complete`, `close`, `done`, `finish`, `start`, `in progress`, `move to`
6. **Add Comment** - `comment`, `note`, `add note`, `mention`

### Tips for Best Results

1. **Use quotes** around values that contain spaces: `"John Doe"`, `"Fix urgent bug"`
2. **Be explicit** with field names: Use `Summary:`, `Assignee:`, `Due Date:`
3. **Include action words**: `create`, `new issue`, `for Create Issue`
4. **Separate multiple fields** with commas
5. **Use natural language**: The system understands context

### Troubleshooting

If the chatbot doesn't extract all fields:
- Check that field names are spelled correctly
- Use quotes around multi-word values
- Ensure there's a clear action word (`create`, `new`, etc.)
- Try rephrasing with explicit field names

### Error Recovery

If fields are missing, the chatbot will ask for clarification:
- "What should be the summary/title for this issue?"
- "Who should this be assigned to?"
- "When is this due?"
