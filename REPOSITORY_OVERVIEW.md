# Repository Structure and Tools

This document provides an overview of the key files and tools available in the repository.

## Edge Extension

### Main Application Files

- `edge-extension/src/manifest.json` - Extension configuration
- `edge-extension/src/html/sidebar.html` - Main UI layout
- `edge-extension/README.md` - Documentation for the extension

### User Interface

- `edge-extension/src/css/sidebar.css` - Styling for the sidebar UI
- `edge-extension/src/images/` - Icons and visual assets

### JavaScript Logic

- `edge-extension/src/js/background.js` - Background service worker for API communication
- `edge-extension/src/js/sidebar.js` - UI interaction logic
- `edge-extension/src/js/content.js` - Content script for web page integration

## Python Server

### Main Application Files

- `python-server/run.py` - Main entry point for the FastAPI server
- `python-server/app/main.py` - FastAPI application configuration
- `python-server/app/api/routes.py` - API route definitions

### Services

- `python-server/app/services/jira_service.py` - Jira API integration service
- `python-server/app/services/oauth_token_service.py` - OAuth token management service

### API Endpoints

- `python-server/app/api/endpoints/jira.py` - Jira API endpoints
- `python-server/app/api/endpoints/oauth.py` - OAuth authentication endpoints

### Models

- `python-server/app/models/jira.py` - Pydantic models for Jira entities

### Static Content

- `python-server/app/static/token_dashboard.html` - OAuth token monitoring dashboard

### Documentation

- `python-server/docs/OAUTH_IMPLEMENTATION.md` - OAuth implementation details
- `python-server/docs/OAUTH2.md` - OAuth 2.0 flow documentation
- `python-server/docs/TOKEN_DASHBOARD.md` - Token dashboard documentation
- `python-server/docs/TOKEN_BACKGROUND_REFRESH.md` - Background token refresh details
- `python-server/docs/REFRESH_TOKENS.md` - Token refresh implementation

### Test and Utility Scripts

- `python-server/test_jira_connection.py` - Tests basic Jira connectivity
- `python-server/test_background_refresh.py` - Tests OAuth background refresh functionality
- `python-server/test_jira_api.py` - Comprehensive Jira API integration test
- `python-server/jira_oauth2_example.py` - Example OAuth 2.0 flow implementation
- `python-server/check_oauth_token.py` - Check the status of the OAuth token
- `python-server/refresh_and_check_token.py` - Force refresh and check the OAuth token
- `python-server/logout_oauth_token.py` - Logout (invalidate) the current OAuth token
- `python-server/token_countdown.py` - Display a countdown to token expiration

## Project Documentation

- `DEVELOPMENT.md` - Development guide
- `start-server.ps1` - PowerShell script to start the FastAPI server
- `documentation/Project_Management_Plan_Microsoft_Edge_Chatbot_Extension_for_Jira.md` - Project management plan
- `documentation/PRD_Microsoft_Edge_Chatbot_Extension_for_Jira_Action_Items3.md` - Product requirements document
- `documentation/Software_Requirements_Specification_Document3.md` - Software requirements specification
- `documentation/User_Interface_Description_Document3.md` - User interface design document

## Environment Files

- `.env` - Environment variables for local development
- `mcp-atlassian.env` - Environment variables for Atlassian API integration

## How to Run

### Start the Server

```powershell
.\start-server.ps1
```

Or manually:

```powershell
cd python-server
.\venv\Scripts\Activate.ps1
python run.py
```

### Access the Token Dashboard

Open a browser and navigate to:
```
http://localhost:8000/dashboard/token
```

### API Documentation

FastAPI auto-generated documentation is available at:
```
http://localhost:8000/docs
```

### Run Tests

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
