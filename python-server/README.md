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
- **OAuth 2.0 Authentication**: Full support for Jira Cloud OAuth 2.0 authentication flow with token refreshing
- **Dual Authentication Methods**: Support for both API token and OAuth 2.0 authentication
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

To test background token refresh functionality:

```powershell
python test_background_refresh.py
```

To test comprehensive Jira API integration:

```powershell
python test_jira_api.py
```

## Token Monitoring Dashboard

The server includes a web-based dashboard for monitoring OAuth token status:

1. Start the server:
   ```powershell
   python run.py
   ```

2. Open the dashboard in your browser:
   ```
   http://localhost:8000/dashboard/token
   ```

The dashboard provides:
- Real-time token status monitoring
- Token refresh statistics
- Event history display
- Jira integration testing features:
  - Project listing functionality
  - Issue retrieval and display

For more details, see `docs/TOKEN_DASHBOARD.md`.

## OAuth 2.0 Setup

1. Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Create a new OAuth 2.0 integration
3. Configure the callback URL (e.g., `http://localhost:8000/api/auth/callback`)
4. Add permissions for Jira API access
5. Copy the client ID and secret to your `.env` file

## OAuth 2.0 Implementation

The OAuth 2.0 implementation follows the Authorization Code Grant flow and includes:

1. **Authorization**: Redirect users to the Atlassian login page to authorize access
2. **Token Exchange**: Exchange authorization code for access and refresh tokens
3. **Token Management**: Store tokens securely and refresh them when they expire
4. **API Integration**: Use tokens with the Atlassian Python API

### Example OAuth Flow

```python
# Initialize OAuth 2.0 session
from requests_oauthlib import OAuth2Session
from app.core.config import settings

# Create OAuth session
oauth = OAuth2Session(
    settings.JIRA_OAUTH_CLIENT_ID,
    scope=["read:jira-user", "read:jira-work", "write:jira-work"],
    redirect_uri=settings.JIRA_OAUTH_CALLBACK_URL
)

# Generate authorization URL
auth_url, state = oauth.authorization_url(
    "https://auth.atlassian.com/authorize",
    audience="api.atlassian.com"
)

# Redirect user to auth_url
# ...

# In the callback handler:
token = oauth.fetch_token(
    "https://auth.atlassian.com/oauth/token",
    code=authorization_code,
    client_secret=settings.JIRA_OAUTH_CLIENT_SECRET
)

# Set token in JiraService
from app.services.jira_service import jira_service
jira_service.set_oauth2_token(token)

# Now you can use the service with OAuth
projects = jira_service.get_projects()
```

For more details, see the OAuth 2.0 example script (`jira_oauth2_example.py`) and the documentation in `docs/OAUTH2.md`.
