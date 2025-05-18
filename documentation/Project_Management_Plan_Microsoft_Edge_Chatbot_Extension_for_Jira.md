# Project Management Plan: Microsoft Edge Chatbot Extension for Jira Action Item Management

## Project Overview
This project involves developing a Microsoft Edge extension with a chatbot interface that enables teams to manage Jira action items through natural language commands. The system will automate task creation, reminders, and evidence tracking while maintaining firewall compliance. The solution leverages the Atlassian Python API for Jira Cloud integration and a free open-source LLM API (OpenRouter) for conversational intelligence.

## Project Structure
- **Edge Extension**: Chromium-based sidebar UI for natural language task management
- **Python Server**: Backend for LLM processing and Jira API communication
- **Atlassian Python API**: Library for Jira Cloud interactions
- **Database**: SQLite for caching task data

## Task Management Instructions
- Tasks are tagged as Done, ToDo, or Backlog
- Priority is indicated by the order in each list
- Tasks must include assignee, due date, and description where applicable

## Development Phases

### Phase 1 (3 weeks): Core Features
- Timeline: May 14, 2025 - June 4, 2025
- Current Date: May 16, 2025 (Day 3 of 21)

#### Completed Tasks
- Initial project requirements gathering
- Creation of PRD, SRS, and UI documentation
- Setup of development environment with VS Code and GitHub Copilot
- Repository structure definition and creation
- Configuration of environment files
- Initial setup of OAuth credentials for Jira Cloud integration

#### Completed Tasks (Updated May 16, 2025)
- Initial project requirements gathering
- Creation of PRD, SRS, and UI documentation
- Setup of development environment with VS Code and GitHub Copilot
- Repository structure definition and creation
- Configuration of environment files
- Initial setup of OAuth credentials for Jira Cloud integration
- Developed Edge extension scaffold with basic UI components
- Set up Python FastAPI server structure with endpoints
- Created testing scripts for Jira API connectivity
- Documented development workflow and setup process

#### In Progress Tasks
1. Set up Atlassian Python API integration (P0) - 80% complete
   - ✅ Configure with Jira Cloud API token
   - ✅ Set up OAuth credentials
   - ✅ Set up Python environment
   - ✅ Document API usage process
   - ⏳ Test basic connectivity to Jira Cloud

2. Enhance Edge extension UI (P0) - 60% complete
   - ✅ Create extension manifest and icon
   - ✅ Implement sidebar structure
   - ✅ Design basic chat interface with input field and response area
   - ⏳ Improve styling and user experience
   - ⏳ Add comprehensive error handling

#### Pending Tasks
1. Complete Python server integration (P0)
   - Implement OpenRouter API integration for LLM capabilities
   - Finalize Atlassian Python API communication
   - Add error handling and retry mechanisms

3. Implement OAuth 2.0 authentication flow (P1)
   - Design login button and authorization flow
   - Handle token storage and refresh

4. Create basic reminder system with browser notifications (P1)
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
| Jira API changes | Medium | High | Use Atlassian Python API which handles versioning, monitor Atlassian announcements |
| OpenRouter API limitations | High | Medium | Implement request throttling, consider fallback LLM options |
| Firewall restrictions | Medium | High | Document network requirements, test in isolated environment |
| OAuth token expiration | Low | Medium | Implement robust token refresh mechanism using Atlassian Python API |
| Browser version compatibility | Low | Medium | Test on multiple Edge versions, use polyfills where needed |

## Team Roles & Responsibilities
- Project Manager: Overall coordination, timeline management, status reporting
- Frontend Developer: Edge extension UI, browser notifications, OAuth flow
- Backend Developer: Python server, LLM integration, Atlassian API integration
- DevOps: Environment setup, intranet deployment, security compliance
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

## Immediate Next Steps (Updated May 18, 2025)

### Day 3-4 (May 16-17, 2025): Project Setup & Environment Configuration - COMPLETED
1. ✅ Set up configuration for OAuth connections
2. ✅ Create basic folder structure for Edge extension
3. ✅ Create basic folder structure for Python FastAPI server
4. ✅ Setup Python environment for development

### Day 5 (May 18, 2025): Integration Testing & Connection Verification - CURRENT PRIORITY
1. Install and set up Atlassian Python API for Jira Cloud integration
   - Install required packages including Atlassian Python API
   - Configure OAuth 2.0 credentials for Jira Cloud access
   - Create test scripts to verify connectivity
   - Document any connection issues and their solutions
2. Verify all components can communicate
   - Ensure Python server can connect to Jira via Atlassian Python API
   - Confirm Edge extension can make requests to Python server

### Day 6-7 (May 19-20, 2025): Edge Extension Enhancement
1. Complete Edge extension UI development
   - Finalize sidebar design with proper styling
   - Implement message streaming for chat responses
   - Create settings configuration page

### Day 8-9 (May 21-22, 2025): Python Server Development
1. Enhance Atlassian Python API integration
   - Create Jira service class using Atlassian Python API
   - Create data models for Jira entities
   - Set up error handling and retry logic
2. Develop LLM integration with OpenRouter
   - Create prompt templates for different use cases
   - Establish API connection with OpenRouter
   - Implement streaming response handling

### Days 9-10 (May 22-23, 2025): Integration & Testing
1. Connect Edge extension to Python server
   - Implement authentication handling
   - Set up WebSocket or polling for real-time updates 
   - Test end-to-end communication flow
2. Create automated tests
   - Unit tests for Python server components
   - Integration tests for critical paths
   - Document testing procedures

### Milestone for Week 1: Completed project infrastructure with functioning Docker container, Edge extension scaffold, and Python server foundation ready for feature development
