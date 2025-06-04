# Software Requirements Specification Document: Microsoft Edge Chatbot Extension for Jira Action Item Management

## System Design
- **Overview**: A client-server system with a Microsoft Edge extension (chatbot UI), a Python backend server, and a sooperset/mcp-atlassian server for Jira Cloud integration, all hosted on an intranet for firewall compliance.
- **Components**:
  - **Edge Extension**: Chromium-based sidebar UI for natural language task management, OAuth 2.0 login, and browser notifications.
  - **Python Server**: FastAPI-based backend for LLM processing (OpenRouter), MCP server communication, and reminder scheduling.
  - **MCP Server**: Docker-based sooperset/mcp-atlassian server handling Jira Cloud interactions via API token.
  - **Database**: SQLite for caching task data and API responses.
- **Deployment**: Intranet server (Ubuntu or Windows) with Docker, outbound HTTPS to OpenRouter and Jira Cloud.

## Architecture Pattern
- **Pattern**: Microservices with a client-server model.
- **Rationale**: Separates concerns (UI, backend logic, Jira integration) for scalability and maintainability. The MCP server acts as a dedicated service for Jira API abstraction.
- **Structure**:
  - **Client (Extension)**: Communicates with Python server via REST API.
  - **Python Server**: Orchestrates LLM requests, MCP server calls, and reminders.
  - **MCP Server**: Standalone service for Jira Cloud interactions, using SSE for real-time updates.
  - **SQLite**: Local storage for caching, reducing external API calls.

## State Management
- **Client (Extension)**:
  - **Local State**: Managed via JavaScript (Vanilla or React) for sidebar state (open/closed, task list sort order), chat history, and OAuth token.
  - **Persistence**: OAuth tokens stored in `chrome.storage.local` for session persistence.
- **Python Server**:
  - **In-Memory**: FastAPI session state for active user requests.
  - **Cached State**: SQLite stores task data and MCP responses for quick retrieval.
- **MCP Server**: Stateless, relying on Jira Cloud for persistent state, with temporary caching in memory for SSE responses.

## Data Flow
- **Task Creation**:
  1. User types command (e.g., “Create task for Alice due Friday”) in extension sidebar.
  2. Extension sends POST to Python server’s `/chat` endpoint.
  3. Python server processes command via OpenRouter LLM, forwards to MCP server via SSE (`http://localhost:9000/sse`).
  4. MCP server creates Jira issue using `jira_create_issue`, returns issue ID.
  5. Python server caches result in SQLite, responds to extension with confirmation (e.g., “Created DOC-42”).
- **Reminders**:
  1. Python server’s APScheduler polls MCP server daily for due tasks (`jira_search`).
  2. MCP server queries Jira Cloud, returns task list.
  3. Python server caches results, sends notifications to extension via WebSocket.
  4. Extension displays browser notifications; user replies (e.g., “Done”) trigger updates via MCP server (`jira_transition_issue`).
- **Evidence Upload**:
  1. User drags file to sidebar’s evidence hub.
  2. Extension sends file to Python server’s `/upload` endpoint.
  3. Python server forwards to MCP server (`jira_add_comment`), which attaches file to Jira issue.
  4. MCP server confirms, and extension updates thumbnail grid.

## Technical Stack
- **Edge Extension**:
  - Languages: JavaScript, HTML, CSS.
  - Frameworks: Vanilla JS (or React for complex state), Chromium APIs (`chrome.runtime`, `chrome.notifications`, `chrome.storage`).
  - Tools: Webpack for bundling, ESLint for linting.
- **Python Server**:
  - Language: Python 3.10+.
  - Framework: FastAPI for REST API, APScheduler for task scheduling.
  - Libraries: `requests` (HTTP), `python-dotenv` (env vars), `sseclient` (SSE), `pydantic` (data validation).
- **MCP Server**:
  - Platform: Docker (image: `ghcr.io/sooperset/mcp-atlassian:latest`).
  - Configuration: `.env` file for API token, SSE transport (`--transport sse --port 9000`).
- **Database**: SQLite (via `sqlite3` Python module).
- **Development**:
  - IDE: VS Code with GitHub Copilot.
  - Version Control: Git (GitHub repository).
  - CI/CD: GitHub Actions for testing/linting.
- **Hosting**: Intranet server (Ubuntu or Windows) with Docker Desktop, Nginx for reverse proxy.

## Authentication Process
- **MCP Server**:
  - Uses Jira Cloud API token, stored in `.env` (`JIRA_USERNAME`, `JIRA_API_TOKEN`).
  - Configured during Docker setup, authenticates all Jira requests.
- **Edge Extension**:
  - OAuth 2.0 for user-specific Jira Cloud access.
  - Flow:
    1. User clicks “Log in with Jira” in sidebar, triggering OAuth flow via Atlassian Developer Console app.
    2. Redirects to Jira login, returns access token to extension.
    3. Token stored in `chrome.storage.local`, sent with API requests to Python server.
    4. Python server forwards token to MCP server for user-authenticated Jira actions.
  - Refresh tokens used for persistent sessions, with `offline_access` scope.

## Route Design
- **Python Server (FastAPI)**:
  - `/chat` (POST): Process natural language commands via LLM, forward to MCP server.
  - `/jira` (POST): Direct MCP server interaction for structured Jira requests.
  - `/upload` (POST): Handle file uploads for Jira issue comments.
  - `/reminders` (GET): Retrieve scheduled reminders for notifications.
  - `/ws/notifications` (WebSocket): Push real-time notifications to extension.
- **Edge Extension**:
  - Internal routes (JavaScript):
    - `/home`: Render sidebar with chat and task list.
    - `/login`: Display OAuth login button and handle redirect.
    - `/notifications`: Manage browser notification display and replies.

## API Design
- **Python Server API**:
  - **POST /chat**:
    - Request: `{ "command": "Create task for Alice due Friday", "user_id": "user123" }`
    - Response: `{ "status": "success", "message": "Created DOC-42", "issue_id": "DOC-42" }`
  - **POST /jira**:
    - Request: `{ "action": "create_issue", "data": { "project": "ACTION-ITEMS", "summary": "Review docs", "assignee": "alice", "due_date": "2025-05-16" } }`
    - Response: `{ "status": "success", "issue_id": "DOC-42" }`
  - **POST /upload**:
    - Request: Multipart form with file and `{ "issue_id": "DOC-42", "user_id": "user123" }`
    - Response: `{ "status": "success", "comment_id": "12345" }`
  - **GET /reminders**:
    - Response: `{ "tasks": [{ "issue_id": "DOC-42", "summary": "Review docs", "due_date": "2025-05-16" }] }`
  - **WebSocket /ws/notifications**:
    - Message: `{ "type": "reminder", "issue_id": "DOC-42", "message": "Due today", "actions": ["Done", "Snooze"] }`
- **MCP Server Interaction**:
  - Uses SSE (`http://localhost:9000/sse`) for commands like `jira_create_issue`, `jira_search`, `jira_add_comment`.
  - Example: `{ "tool": "jira_create_issue", "params": { "project": "ACTION-ITEMS", "summary": "Review docs" } }`

## Database Design ERD
- **Database**: SQLite (single file, `tasks.db`).
- **Tables**:
  - **Tasks**:
    - `id` (INTEGER, PRIMARY KEY): Unique task ID.
    - `issue_id` (TEXT): Jira issue ID (e.g., “DOC-42”).
    - `summary` (TEXT): Task title (e.g., “Review docs”).
    - `assignee` (TEXT): User ID or email.
    - `due_date` (TEXT): ISO date (e.g., “2025-05-16”).
    - `status` (TEXT): Jira status (e.g., “To Do”, “Done”).
    - `last_updated` (TEXT): Timestamp for cache refresh.
  - **Cache**:
    - `key` (TEXT, PRIMARY KEY): API request hash (e.g., “jira_search:assignee=alice”).
    - `response` (TEXT): JSON response from MCP server.
    - `timestamp` (TEXT): Cache expiry timestamp.
- **Relationships**:
  - No direct relationships; Tasks table stores Jira data, Cache table stores transient API responses.
- **Usage**:
  - Tasks: Cache frequently accessed tasks for reminders and queries.
  - Cache: Store MCP server responses (e.g., task lists) for 1 hour to reduce API calls.
