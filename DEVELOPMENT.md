# Development Guide: Microsoft Edge Chatbot Extension for Jira

This guide provides detailed instructions for developers working on the Microsoft Edge Chatbot Extension for Jira Action Item Management project.

## Project Overview

We're building a Microsoft Edge extension with a chatbot interface for managing Jira action items using natural language. The system consists of:

1. **Edge Extension**: The frontend UI that users interact with (✅ Complete)
2. **Python FastAPI Server**: The backend that processes user requests and communicates with both the LLM and Jira (✅ Complete)
3. **Atlassian Python API**: Library that interfaces with Jira Cloud APIs (✅ Complete)
4. **SQLite Database**: Local storage for caching data and multi-user support (✅ Complete)
5. **OpenRouter LLM Integration**: Natural language processing (✅ Complete)

## Current Status (June 13, 2025) - Phase 1 COMPLETED

### ✅ Phase 1 Completed Components (ALL OBJECTIVES ACHIEVED)
- **OAuth 2.0 Multi-User Authentication**: Full implementation with encrypted token storage
- **Edge Extension UI**: Sidebar interface with chat functionality and bug fixes
- **Python Server**: FastAPI with comprehensive API endpoints and database integration
- **Jira Integration**: Complete Atlassian Python API integration with testing
- **LLM Integration**: OpenRouter chat functionality with natural language processing
- **Dynamic URL System**: Support for both localhost and ngrok configurations
- **Testing Infrastructure**: Comprehensive debugging and monitoring tools

### 🎯 Phase 2 Development Priority
**Enhanced Features Development** - Next phase focuses on advanced functionality including file uploads, complex queries, and custom reminder templates.

## Development Environment Setup

### Prerequisites

- Git
- Python 3.9+
- Node.js 18+ (for extension development)
- VS Code (recommended)
- PowerShell (with ExecutionPolicy configured - see troubleshooting section)
- Microsoft Edge (version 88+)
- PowerShell 7.0+ (for automation scripts)

### Initial Setup

1. **Clone the repository**:
   ```powershell
   git clone <repository-url>
   cd jcai-v2
   ```

2. **Configure Jira credentials**:
   - Ensure `.env` file is properly configured with Jira credentials
   - Set up OAuth 2.0 credentials in the [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
   - Configure the credentials in the `.env` file:
     ```
     JIRA_OAUTH_CLIENT_ID=your_client_id
     JIRA_OAUTH_CLIENT_SECRET=your_client_secret
     JIRA_OAUTH_CALLBACK_URL=http://localhost:8000/api/auth/jira/callback
     ```

3. **Set up Python server**:
   ```powershell
   cd python-server
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install atlassian-python-api requests-oauthlib
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the server with convenience script**:
   ```powershell
   .\start-server.ps1
   ```
   This script activates the virtual environment and starts the FastAPI server.

4. **Load Edge extension for development**:
   - Open Edge browser and navigate to `edge://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select `edge-extension/src` folder

## Running the Application

1. **Start Python FastAPI server**:
   ```powershell
   .\start-server.ps1
   ```
   Or manually start it:
   ```powershell
   cd python-server
   .\venv\Scripts\Activate.ps1
   python run.py
   ```

   The server includes comprehensive logging for OAuth token events in `oauth_token_service.log`.
   The API will be available at:
   - API Documentation: `http://localhost:8000/docs`
   - Token Dashboard: `http://localhost:8000/dashboard/token`

2. **Test the Edge extension**:
   The extension should be available in your Edge browser. Click the extension icon to open the sidebar.

3. **Test Jira API Connection**:
   Several test scripts are available to test different aspects of the API:
   ```powershell
   cd python-server
   .\venv\Scripts\Activate.ps1

   # Basic connectivity test
   python test_jira_connection.py

   # OAuth background refresh test
   python test_background_refresh.py

   # Comprehensive Jira API test
   python test_jira_api.py
   ```

## Development Workflow

### Atlassian Python API Development

- The Atlassian Python API is a Python library that provides access to Jira Cloud APIs
- To check if it's working correctly, run:
  ```powershell
  cd python-server
  python test_jira_connection.py
  ```
- To test OAuth 2.0 flow:
  ```powershell
  cd python-server
  python jira_oauth2_example.py
  ```
- To test background token refresh:
  ```powershell
  cd python-server
  python test_background_refresh.py
  ```
- To check token status:
  ```powershell
  cd python-server
  python check_oauth_token.py
  ```
- Key features of Atlassian Python API:
  - Support for Jira Cloud and Server
  - OAuth 2.0 authentication support
  - Comprehensive access to Jira REST APIs
  - Well-documented examples in the [GitHub repository](https://github.com/atlassian-api/atlassian-python-api)

### Python Server Development

1. **API Endpoints**
   - Add new endpoints in `python-server/app/api/endpoints/`
   - Register them in `python-server/app/api/routes.py`

2. **Services**
   - Business logic should be in `python-server/app/services/`
   - `jira_service.py`: Handles communication with Jira using Atlassian Python API
   - `llm_service.py`: Handles communication with OpenRouter LLM
   - `chat_service.py`: Processes chat messages and orchestrates responses

3. **Data Models**
   - Define Pydantic models in `python-server/app/models/`

### Edge Extension Development

1. **UI Components**
   - HTML templates in `edge-extension/src/html/`
   - CSS styles in `edge-extension/src/css/`

2. **JavaScript Logic**
   - Background script in `edge-extension/src/js/background.js`
   - Sidebar UI logic in `edge-extension/src/js/sidebar.js`

3. **Extension Configuration**
   - Manifest in `edge-extension/src/manifest.json`

## Coding Standards

1. **Python Code**
   - Follow PEP 8 style guide
   - Use async/await for asynchronous operations
   - Document functions with docstrings

2. **JavaScript Code**
   - Use ES6+ features
   - Follow camelCase naming convention
   - Comment complex logic

3. **CSS**
   - Use BEM naming convention
   - Keep styles modular and reusable

## Testing

### 1. Multi-User System Testing
   **OAuth Multi-User Flow Testing**:
   ```powershell
   cd python-server
   .\venv\Scripts\Activate.ps1

   # Test multi-user OAuth endpoints
   python test_multi_user_oauth.py

   # Test user management
   python test_user_management.py
   ```

### 2. Component Testing
   **Atlassian Python API integration**: Use the provided test scripts
   ```powershell
   # Test basic connectivity
   python python-server/test_jira_connection.py

   # Test OAuth configuration
   python python-server/check_oauth_token.py

   # Test background refresh
   python python-server/test_background_refresh.py

   # Test token refresh
   python python-server/refresh_and_check_token.py
   ```

   **Python server**: Run unit tests
   ```powershell
   cd python-server
   python -m pytest tests/
   ```

   **Edge extension**: Use the browser's developer tools (F12) to debug
   - Test tab responsiveness with `edge-extension/test-final-fixes.html`
   - Verify context handling with automated test scripts

### 3. Extension Bug Fix Verification
   **Tab Responsiveness Testing**:
   ```powershell
   cd edge-extension
   .\test_fixes.ps1
   ```

   **Context Invalidation Testing**:
   - Open `edge-extension/test-final-fixes.html` in Edge
   - Test extension reload scenarios
   - Verify error handling in content scripts

### 4. Manual Testing
   - Test all features on Microsoft Edge latest version
   - Verify both online and offline behavior
   - Check responsive design for various sidebar widths
   - Test natural language commands for different Jira operations

3. **Integration Testing**
   - Verify end-to-end flow from UI to LLM to Jira and back
   - Test error handling when services are unavailable
   - Check authentication token refresh mechanisms
   - Use the Token Dashboard to monitor OAuth status in real-time

## Deployment

### Development Deployment

- The extension can be loaded as an unpacked extension in Edge
- The Python server runs locally on your machine
- The Atlassian Python API is included in the Python environment

### Production Deployment

- Package the Edge extension for the Microsoft Store
- Deploy the Python server to a company intranet server
- Ensure the Atlassian Python API is installed on the production server

## Token Monitoring Dashboard

The project includes a web-based dashboard for monitoring the status of OAuth tokens and testing Jira API integration.

### Accessing the Dashboard

The token dashboard is available at:
```
http://localhost:8000/dashboard/token
```

### Dashboard Features

- Real-time token status monitoring with expiration countdown
- Token refresh statistics and event log
- Jira integration testing:
  - Project listing functionality
  - Issue retrieval and display
  - Interactive project selection and issue viewing

For detailed information, see `python-server/docs/TOKEN_DASHBOARD.md`

## Troubleshooting

### Helper Scripts

We've created several helper scripts to simplify development tasks:

1. **jcai-tools.ps1** - A menu-driven tool for common tasks
   - Run with: `.\jcai-tools.ps1`
   - Provides access to all common operations

2. **run_server_fixed.ps1** - Properly starts the Python server
   - Run with: `.\run_server_fixed.ps1`
   - Handles environment activation and directory switching

3. **validate_environment.ps1** - Checks your development setup
   - Run with: `.\validate_environment.ps1`
   - Validates Python, Node.js, and other dependencies

4. **run_oauth_troubleshooter.ps1** - Runs the OAuth troubleshooting tool
   - Run with: `.\run_oauth_troubleshooter.ps1`
   - Helps diagnose OAuth authentication issues

### Common Issues

1. **Atlassian Python API Connection Problems**
   - Verify the Jira credentials in the environment file
   - Ensure OAuth setup has been completed if using OAuth
   - Check if Atlassian Python API is properly installed
   - Verify network connectivity to Jira Cloud
   - Use the token dashboard to check token status

2. **Python Server Issues**
   - Check if virtual environment is activated
   - Verify `.env` file has correct configuration
   - Ensure required ports are not already in use
   - Use `.\validate_environment.ps1` to check environment setup

3. **Edge Extension Issues**
   - Check browser console for JavaScript errors
   - Verify the extension is properly loaded in `edge://extensions/`
   - Ensure the manifest.json is valid

4. **PowerShell Execution Policy Issues**
   - If scripts can't run due to execution policy, use:
     ```powershell
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     ```
   - This sets the policy temporarily for the current terminal session
   - Alternatively, use our helper scripts which include this command

## OAuth 2.0 Implementation

### Overview

We've implemented OAuth 2.0 authentication for secure communication with Atlassian Jira Cloud APIs. This implementation:

1. Follows the Authorization Code Grant flow
2. Handles token refreshing automatically via dedicated background thread
3. Provides secure storage of access and refresh tokens
4. Integrates with the Atlassian Python API
5. Provides monitoring and management dashboard

### Setup Steps

1. **Register an OAuth App in Atlassian Developer Console**
   - Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
   - Create a new OAuth 2.0 integration
   - Configure the callback URL (e.g., `http://localhost:8000/callback`)
   - Request the necessary scopes (read/write)
   - Note your Client ID and Client Secret

2. **Configure Environment Variables**
   - Update the `.env` file with your OAuth credentials:
     ```
     JIRA_OAUTH_CLIENT_ID=your_client_id
     JIRA_OAUTH_CLIENT_SECRET=your_client_secret
     JIRA_OAUTH_CALLBACK_URL=http://localhost:8000/api/auth/jira/callback
     ```

3. **Test OAuth Flow**
   - Run the OAuth example script:
     ```powershell
     cd python-server
     .\venv\Scripts\Activate.ps1
     python jira_oauth2_example.py
     ```
   - Open `http://localhost:8000` in your browser
   - Click "Login" to initiate the OAuth flow
   - Grant permission when redirected to Atlassian

4. **Test Background Token Refresh**
   - Run the background refresh test script:
     ```powershell
     cd python-server
     .\venv\Scripts\Activate.ps1
     python test_background_refresh.py
     ```

5. **Access the Token Monitoring Dashboard**
   - Start the server with `python run.py`
   - Open `http://localhost:8000/dashboard/token` in your browser

### Implementation Details

The OAuth 2.0 implementation includes several components:

1. **OAuthTokenService** (`app/services/oauth_token_service.py`)
   - Dedicated background thread for token monitoring
   - Automatic refresh before token expiration
   - Event notification system for token events
   - Comprehensive logging and retry mechanisms

2. **JiraService Integration** (`app/services/jira_service.py`)
   - OAuth token management with cloud ID resolution
   - Client initialization with token integration
   - Cross-platform compatible API access
   - Error handling and retry mechanisms

3. **API Endpoints** (`app/api/endpoints/oauth.py`)
   - Token status and management endpoints
   - Jira project and issue retrieval endpoints
   - Token event history endpoint

4. **Token Monitoring Dashboard** (`app/static/token_dashboard.html`)
   - Real-time token status display
   - Token refresh statistics
   - Jira API testing interface
   - Project and issue browser

For detailed documentation, see:
- `python-server/docs/OAUTH_IMPLEMENTATION.md`
- `python-server/docs/TOKEN_DASHBOARD.md`
- `python-server/docs/OAUTH2.md`
- `python-server/docs/REFRESH_TOKENS.md`

## Multi-User Implementation

### Overview
The system now supports multiple users with individual OAuth tokens and secure data isolation. Each user has their own encrypted token storage and independent Jira access.

### Key Features
- **Encrypted Token Storage**: Uses Fernet encryption for sensitive OAuth data
- **User Management**: SQLAlchemy models for User and OAuthToken entities
- **API Versioning**: Multi-user endpoints at `/api/auth/oauth/v2/*` and `/api/jira/v2/*`
- **Data Isolation**: Each user's data is completely separated
- **Background Token Refresh**: Automatic token renewal for all users

### Database Schema
```sql
Users Table:
- id (Primary Key)
- username (Unique)
- email
- created_at
- updated_at

OAuthTokens Table:
- id (Primary Key)
- user_id (Foreign Key)
- encrypted_access_token
- encrypted_refresh_token
- cloud_id
- expires_at
- created_at
- updated_at
```

### Multi-User API Endpoints
- `POST /api/auth/oauth/v2/login/{user_id}` - Initiate OAuth for specific user
- `GET /api/auth/oauth/v2/callback` - Handle OAuth callback
- `GET /api/auth/oauth/v2/status/{user_id}` - Check auth status for user
- `GET /api/jira/v2/projects/{user_id}` - Get projects for specific user
- `GET /api/jira/v2/issues/{user_id}` - Get issues for specific user

For detailed implementation details, see: `python-server/MULTI_USER_IMPLEMENTATION.md`

## Next Development Phase: Phase 2 Enhanced Features

### Priority Tasks for Phase 2 Implementation

#### 1. File Upload Capability for Evidence Attachment (P0)
```powershell
# Implementation areas:
# - Edge extension: Drag-and-drop interface in sidebar
# - Python server: File processing and storage endpoints
# - Jira integration: Attachment API via Atlassian Python API
```

#### 2. Advanced Query Functionality (P1)
```powershell
# Natural language query examples:
# - "Show me overdue tasks assigned to John"
# - "Find all bugs created this week"
# - "What tasks are due tomorrow?"
```

#### 3. Custom Reminder Templates with @mentions (P1)
```powershell
# Features to implement:
# - Template system for reminder messages
# - @mention parsing and notification routing
# - Snooze functionality with smart intervals
```

#### 4. Performance Optimization (P2)
```powershell
# Optimization areas:
# - Query caching for frequent requests
# - Database indexing for large datasets
# - Extension startup time improvements
```

### Development Timeline for Phase 2
- **Week 1-2 (June 14-27)**: File upload system implementation
- **Week 3-4 (June 28-July 11)**: Advanced query functionality
- **Week 5 (July 12-18)**: Custom reminder templates and optimization

### Ready-to-Use Components from Phase 1
All Phase 1 components are production-ready and can be leveraged for Phase 2 development:
- **Multi-user OAuth system**: Handles authentication for file uploads
- **LLM integration**: Can process natural language for complex queries
- **Jira API integration**: Ready for attachment and advanced query operations
- **Database system**: Prepared for caching and performance optimization
