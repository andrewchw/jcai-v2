# Python Server for Microsoft Edge Chatbot Extension for Jira

This directory contains the FastAPI backend server for the Microsoft Edge Chatbot Extension for Jira, which integrates with Jira Cloud using the Atlassian Python API.

## Setup Instructions

1. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```

3. Configure the environment variables:
   ```powershell
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the server:
   ```powershell
   python run.py
   ```

The server will start at `http://localhost:8000` with API documentation available at `http://localhost:8000/docs`.

## Key Features

- **Jira API Integration**: Using the Atlassian Python API library to interact with Jira
- **OAuth 2.0 Authentication**: Support for Jira Cloud OAuth 2.0 authentication
- **FastAPI Framework**: Modern, high-performance web framework for building APIs
- **Async Processing**: Asynchronous request handling for better performance

## Directory Structure

- `app/`: Main application package
  - `api/`: API endpoints and routes
    - `endpoints/`: Individual API endpoint modules
  - `core/`: Core application components (config, etc.)
  - `models/`: Pydantic data models
  - `services/`: Business logic services
- `tests/`: Unit and integration tests

## Authentication

Two authentication methods are supported:

1. **API Token**: For server-to-server integration, using JIRA_USERNAME and JIRA_API_TOKEN
2. **OAuth 2.0**: For user-based authentication, using JIRA_OAUTH_CLIENT_ID and JIRA_OAUTH_CLIENT_SECRET

## Testing

To test Jira API connectivity:

```powershell
python test_jira_connection.py
```

To test OAuth 2.0 authentication:

```powershell
python jira_oauth2_example.py
```

## OAuth 2.0 Setup

1. Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Create a new OAuth 2.0 integration
3. Configure the callback URL (e.g., `http://localhost:8000/api/auth/callback`)
4. Add permissions for Jira API access
5. Copy the client ID and secret to your `.env` file
