# Product Requirements Document: Intelligent Microsoft Edge Chatbot Extension for Jira Action Item Management

## 1. Elevator Pitch
An Edge extension chatbot that enables teams to manage Jira action items through natural language commands, automating task creation, reminders, and evidence tracking while maintaining firewall compliance. This solution leverages the sooperset/mcp-atlassian server to simplify Jira Cloud integration and a free open-source LLM API (e.g., OpenRouter) for conversational intelligence, reducing manual Jira updates by 80% and supporting seamless task management directly in Microsoft Edge.

## 2. Who Is This App For
- Team leads managing distributed agile teams
- Developers/QA engineers needing quick task updates
- Project managers tracking sprint deliverables
- IT departments requiring firewall-compliant solutions
- Organizations restricted to Microsoft Edge browser

## 3. Functional Requirements

### Core Features (Phase 1)
- **Conversational Task Management**: Natural language commands to create, update, and query Jira issues via the sooperset/mcp-atlassian server, abstracting Jira REST API complexity.
- **LLM Integration**: OpenRouter’s free API (e.g., Llama 3, Mistral 7B) for parsing user input and generating context-aware responses, integrated with the MCP server for Jira actions.
- **Reminders**: Browser notifications to task owners based on Jira due dates, with conversational reply support (e.g., “Done”, “Need extension”) processed via the MCP server.
- **Evidence Upload**: File upload and comment support, attaching evidence to Jira issues through the MCP server’s `jira_add_comment` tool.
- **Intranet Hosting**: Python server and MCP server hosted internally, ensuring firewall compliance, with the MCP server handling Jira Cloud interactions.
- **Edge Extension**: Chromium-based sidebar or popup chat interface, authenticating users via OAuth 2.0 for personalized Jira access.

### Enhanced Features (Phase 2)
- Advanced file upload with OCR validation for evidence, leveraging MCP server’s attachment capabilities.
- Multi-criteria task queries (e.g., “Show Sarah’s overdue docs review”) using MCP server’s `jira_search` tool with JQL.
- Custom reminder templates with @mentions, processed via the MCP server.

### Advanced Features (Phase 3)
- Predictive task prioritization using historical data from MCP server’s `jira_get_issue` and `jira_batch_get_changelogs`.
- Cross-project dependency mapping via MCP server’s project queries.
- SLA compliance analytics dashboard built on MCP server data.

### Technical Requirements
- **Extension (Client)**:
  - JavaScript, HTML, CSS; uses Chromium APIs (`chrome.runtime`, `chrome.notifications`).
  - OAuth 2.0 authentication for individual user logins to Jira Cloud, integrated with the MCP server.
- **Python Server**:
  - Python 3.x with FastAPI; libraries include `requests`, `APScheduler`, `python-dotenv`.
  - Communicates with the MCP server via SSE (`http://localhost:9000/sse`) or stdio for Jira actions.
- **MCP Server (sooperset/mcp-atlassian)**:
  - Docker-based, hosted locally on intranet (e.g., `ghcr.io/sooperset/mcp-atlassian:latest`).
  - Uses API token for Jira Cloud authentication, configured via `.env` file.
  - Supports tools: `jira_create_issue`, `jira_update_issue`, `jira_search`, `jira_add_comment`, `jira_transition_issue`.
- **Database**: SQLite for local caching of tasks and MCP server responses.
- **Authentication**:
  - **Server**: Jira Cloud API token for MCP server, stored securely in `.env`.
  - **Extension**: OAuth 2.0 for user-specific Jira access, with tokens managed by the MCP server.
- **Hosting**: Intranet server (Linux/Windows), outbound HTTPS only to OpenRouter’s API and Jira Cloud (via MCP server).
- **Development Environment**: VS Code with GitHub Copilot, Docker Desktop for MCP server.

## 4. User Stories

### High-Priority Stories
- As a team lead, I want to type "Create a task for John to review docs by Monday" in the Edge extension, so the bot uses the MCP server to create a Jira issue without manual REST API setup.
- As a task owner, I want to receive browser notifications with natural language reminders and confirm completion conversationally in the extension, with the MCP server updating Jira.
- As a team member, I want to ask "What tasks are assigned to me?" in the extension after OAuth login, so the MCP server queries Jira and returns my tasks.
- As a Scrum Master, I want to type "Log retrospective action items for Sprint 22" and have tasks auto-created with assignees via the MCP server, eliminating manual Jira entry.
- As a Developer, I want to respond "Done" to a chatbot reminder notification, so the MCP server closes the Jira ticket using `jira_transition_issue`.
- As a PMO, I need to ask "Show all unapproved PRDs" after OAuth login, so the MCP server returns linked Jira issues with statuses, avoiding direct Jira navigation.

### Technical Stories
- As a DevOps Engineer, I want CLI deployment of the intranet Python and MCP servers with health checks, ensuring firewall compliance and MCP server availability.
- As a Security Officer, I require the MCP server to use a Jira API token stored on-prem and OAuth 2.0 for user authentication in the extension, ensuring secure access.
- As a Developer, I want the MCP server to handle Jira REST API errors transparently, so my Python server only processes successful responses or clear error messages.

## 5. User Interface

**Chat UI (Edge Sidebar):**
```
[Bot Icon] Log in with Jira to start tracking tasks
[OAuth Login Button]
User: "Assign docs review to Alice due Friday"
Bot: "Created Jira DOC-42 • Due May 16 • Reminders set"
```
**Key Components:**
- OAuth login button for user authentication via Jira Cloud.
- Context-aware input with auto-suggestions for project IDs and assignees, powered by MCP server’s `jira_search` metadata.
- Visual proof hub: thumbnail grid of uploaded evidence via MCP server’s `jira_add_comment`.
- SLA meter: color-coded due date progress bar based on MCP server data.
- Browser notifications with actionable replies, triggering MCP server actions.

## 6. Success Metrics
- Reduce manual task reminders by 80% using MCP server automation.
- 100% of action items tracked in Jira via the extension and MCP server.
- Users can create, query, or complete tasks in under 30 seconds using natural language through the MCP server.
- Zero missed reminders for due tasks, driven by MCP server queries.

## 7. Development Scope

| Phase   | Focus                                         | Timeline |
|---------|-----------------------------------------------|----------|
| Phase 1 | Core: Edge extension, chat UI, LLM/MCP/Jira integration, reminders | 3 weeks  |
| Phase 2 | File upload, advanced MCP queries, enhanced prompts | 5 weeks  |
| Phase 3 | Performance, firewall testing, analytics, UX   | 8 weeks  |

## 8. Constraints
- Restricted to Microsoft Edge browser per company policy.
- Python and MCP servers must be hosted on intranet due to firewall restrictions, with external calls limited to OpenRouter’s API and Jira Cloud (via MCP server).
- Limited to OpenRouter’s free API tier to avoid costs, which may impose rate limits.
- Team must have basic familiarity with Jira workflows and OAuth setup.

## 9. Assumptions
- OpenRouter’s free API supports sufficient throughput for team usage (can fallback to Groq if needed).
- Jira Cloud instance is accessible via API token for the MCP server and OAuth 2.0 for user logins.
- Intranet server has Python 3.x, Node.js (for extension build tools), Docker, and required dependencies installed.
- Edge browser is managed to allow extension installation via enterprise policies.
- sooperset/mcp-atlassian server supports all required Jira actions (create, update, query, comment) for the use case.

## 10. Development Plan

- **Setup:**
  - Configure VS Code with Copilot, install Python, Node.js, and Docker Desktop.
  - Register for OpenRouter API key and Jira Cloud API token.
  - Set up OAuth 2.0 app in Atlassian Developer Console for extension user logins.
  - Deploy sooperset/mcp-atlassian server locally: `docker pull ghcr.io/sooperset/mcp-atlassian:latest`.
  - Configure MCP server with `.env`:
    ```
    JIRA_URL=https://your-company.atlassian.net
    JIRA_USERNAME=your.email@company.com
    JIRA_API_TOKEN=your_jira_api_token
    JIRA_PROJECTS_FILTER=ACTION-ITEMS
    MCP_VERBOSE=true
    ```
- **Code Structure:**
  - **Extension**:
    - JavaScript for chat UI, OAuth 2.0 login flow, and API calls to Python server.
    - Browser notifications with replies, forwarding to Python server.
  - **Python Server**:
    - FastAPI endpoints: `/chat` (LLM processing), `/jira` (MCP server interaction), `/reminders` (scheduling).
    - SSE client to connect to MCP server (`http://localhost:9000/sse`).
    - APScheduler to poll MCP server for due tasks and send notifications.
  - **MCP Server**:
    - Docker container running locally, handling Jira Cloud interactions.
    - Tools: `jira_create_issue`, `jira_search`, `jira_update_issue`, `jira_add_comment`, `jira_transition_issue`.
- **Testing:**
  - Use VS Code debugging for extension and Python server.
  - Test MCP server locally with sample commands (e.g., `jira_create_issue`).
  - Simulate OAuth user logins and Jira responses via MCP server.
  - Verify notification delivery in Edge.
- **Deployment:**
  - Deploy Python and MCP servers on intranet (e.g., Ubuntu server with FastAPI, Docker, SQLite).
  - Run MCP server: `docker run --rm -p 9000:9000 --env-file .env ghcr.io/sooperset/mcp-atlassian:latest --transport sse --port 9000 -vv`.
  - Package extension as a `.crx` file and distribute via enterprise policy (e.g., `ExtensionInstallForceList`).
  - Configure firewall to allow outbound HTTPS to OpenRouter’s API and Jira Cloud.

## 11. Risks and Mitigation

| Risk                                              | Mitigation                                                                                   |
|---------------------------------------------------|----------------------------------------------------------------------------------------------|
| OpenRouter’s free tier rate limits slow responses | Cache frequent MCP server queries in SQLite or fallback to alternative free LLM APIs (e.g., Groq). |
| MCP server fails to handle complex Jira actions   | Test all required tools (`jira_create_issue`, `jira_search`, etc.) locally; contribute fixes to sooperset/mcp-atlassian if needed. |
| OAuth 2.0 setup complexity for extension users    | Provide clear setup guide for Atlassian OAuth app; use MCP server’s OAuth wizard for initial config. |
| Firewall blocks OpenRouter or Jira Cloud API calls | Work with IT to allow outbound traffic to OpenRouter and Jira Cloud endpoints.               |
| Enterprise policies restrict extension install    | Use group policies to enable self-hosted extension deployment.                               |

## 12. Timeline & Resources

- **Timeline**: 6-8 weeks for Phase 1 (core functionality), assuming 1-2 developers.
- **Resources**:
  - Developer(s) with Python, JavaScript, and Docker experience.
  - Jira admin for API token and OAuth app setup.
  - IT support for intranet server, Docker, and firewall configuration.
  - Edge enterprise admin for extension deployment policies.

---
