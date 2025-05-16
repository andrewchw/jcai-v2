# Project Management Plan: Microsoft Edge Chatbot Extension for Jira Action Item Management

## Project Overview
This project involves developing a Microsoft Edge extension with a chatbot interface that enables teams to manage Jira action items through natural language commands. The system will automate task creation, reminders, and evidence tracking while maintaining firewall compliance. The solution leverages the sooperset/mcp-atlassian server for Jira Cloud integration and a free open-source LLM API (OpenRouter) for conversational intelligence.

## Project Structure
- **Edge Extension**: Chromium-based sidebar UI for natural language task management
- **Python Server**: Backend for LLM processing and MCP server communication
- **MCP Server**: Docker-based server handling Jira Cloud interactions
- **Database**: SQLite for caching task data

## Task Management Instructions
- Tasks are tagged as Done, ToDo, or Backlog
- Priority is indicated by the order in each list
- Tasks must include assignee, due date, and description where applicable

## Development Phases

### Phase 1 (3 weeks): Core Features
- Timeline: May 14, 2025 - June 4, 2025

#### Completed Tasks
- Initial project requirements gathering
- Creation of PRD, SRS, and UI documentation
- Setup of development environment with VS Code and GitHub Copilot
- Repository structure definition and creation

#### Pending Tasks
1. Set up the Docker environment for the MCP server (P0)
   - Configure with Jira Cloud API token
   - Test basic connectivity to Jira Cloud

2. Develop Edge extension scaffold with sidebar UI (P0)
   - Create extension manifest and icon
   - Implement sidebar toggle functionality
   - Design basic chat interface with input field and response area

3. Build Python server with FastAPI (P0)
   - Set up endpoints for chat, Jira interactions, and file uploads
   - Implement OpenRouter API integration
   - Create MCP server communication via SSE

4. Implement OAuth 2.0 authentication flow (P1)
   - Design login button and authorization flow
   - Handle token storage and refresh

5. Create basic reminder system with browser notifications (P1)
   - Implement APScheduler for polling due tasks
   - Set up browser notification display and interaction

#### Backlog Tasks
- Implement SQLite database for caching
- Add error handling and retry logic for API calls
- Create user documentation for extension installation

### Phase 2 (5 weeks): Enhanced Features
- Timeline: June 5, 2025 - July 10, 2025

#### Pending Tasks
1. Develop file upload capability for evidence attachment (P0)
   - Implement drag-and-drop interface
   - Create thumbnail grid for uploaded evidence
   - Add MCP server integration for Jira attachments

2. Build advanced query functionality (P1)
   - Implement multi-criteria task queries
   - Create natural language parsing for complex queries
   - Add query result caching

3. Design and implement custom reminder templates (P1)
   - Allow for @mentions in reminders
   - Create customizable notification templates
   - Add snooze functionality

#### Backlog Tasks
- Add support for task sorting and filtering in sidebar
- Implement keyboard shortcuts for common actions
- Create visual SLA progress indicators

### Phase 3 (8 weeks): Advanced Features
- Timeline: July 11, 2025 - September 5, 2025

#### Pending Tasks
1. Develop predictive task prioritization (P0)
   - Implement historical data analysis
   - Create algorithm for suggesting task priority
   - Design UI for displaying recommendations

2. Build cross-project dependency mapping (P1)
   - Implement visualization of task dependencies
   - Add ability to create and modify dependencies
   - Create filtering options for dependency view

3. Create SLA compliance analytics dashboard (P2)
   - Design metrics visualization components
   - Implement data collection and processing
   - Add export functionality for reports

#### Backlog Tasks
- Add support for bulk operations on tasks
- Implement advanced OCR for evidence validation
- Create team performance analytics

## Testing Strategy
- Unit tests for all components with 80% code coverage minimum
- Integration tests for all API endpoints
- End-to-end testing of the complete flow
- Performance testing under load
- User acceptance testing with team leads and developers

## Deployment Plan
1. Internal deployment to test server (Week 1 of each phase)
2. QA testing and bug fixes (Week 2 of each phase)
3. Limited user testing (Week 3 of each phase)
4. Full deployment to production environment (Final week of each phase)

## Risk Management

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Jira API changes | Medium | High | Implement version checking, monitor Atlassian announcements |
| OpenRouter API limitations | High | Medium | Implement request throttling, consider fallback LLM options |
| Firewall restrictions | Medium | High | Document network requirements, test in isolated environment |
| OAuth token expiration | Low | Medium | Implement robust token refresh mechanism |
| Browser version compatibility | Low | Medium | Test on multiple Edge versions, use polyfills where needed |

## Team Roles & Responsibilities
- Project Manager: Overall coordination, timeline management, status reporting
- Frontend Developer: Edge extension UI, browser notifications, OAuth flow
- Backend Developer: Python server, LLM integration, MCP server communication
- DevOps: Docker setup, intranet deployment, security compliance
- QA Engineer: Testing strategy, test case development, bug verification

## Communication Plan
- Daily standup: 15 minutes, 9:00 AM
- Weekly progress review: 1 hour, Mondays at 11:00 AM
- Monthly stakeholder demo: 1 hour, last Friday of each month
- Issue tracking: Jira board with up-to-date status
- Documentation: Shared repository with living documents

## Success Criteria
- Reduce manual task reminders by 80%
- 100% of action items tracked in Jira via the extension
- Users able to create, query, or complete tasks in under 30 seconds
- Zero missed reminders for due tasks
- Firewall compliance maintained throughout deployment
