# OAuth 2.0 Implementation Documentation

## Overview

This document describes the OAuth 2.0 implementation for the Microsoft Edge Chatbot Extension for Jira project.
The implementation includes token management, background refresh, and monitoring capabilities.

## Architecture

The OAuth 2.0 implementation consists of the following components:

1. **OAuthTokenService** - A dedicated service for OAuth token management with background refresh
2. **JiraService Integration** - Integration with the OAuthTokenService in the JiraService class
3. **Token Monitoring Dashboard** - A web interface for monitoring token status
4. **API Endpoints** - Endpoints for token status and management

## Components

### OAuthTokenService

The `OAuthTokenService` class (`app/services/oauth_token_service.py`) provides:

- Dedicated background thread for continuous token monitoring
- Configurable check intervals (default: 5 minutes)
- Configurable refresh thresholds (default: 10 minutes before expiration)
- Event notification system for token-related events
- Retry mechanisms for failed refreshes with exponential backoff
- Comprehensive logging of token events

### JiraService Integration

The `JiraService` class (`app/services/jira_service.py`) integrates with the `OAuthTokenService`:

- Initializes the token service during startup
- Uses the token service for token storage and retrieval
- Provides methods for manual token refresh
- Ensures proper cleanup of background threads on application shutdown

### Token Monitoring Dashboard

The token monitoring dashboard (`app/static/token_dashboard.html`) provides:

- Real-time display of token status
- Countdown to token expiration
- Token refresh statistics
- Event history display
- Manual token refresh capability
- Jira integration testing features:
  - Project listing to validate OAuth token connectivity
  - Issue retrieval to test API access with OAuth token

### API Endpoints

The API endpoints (`app/api/endpoints/oauth.py`) include:

- **GET /auth/oauth/token/status** - Get current token status
- **POST /auth/oauth/token/refresh** - Manually refresh the token
- **GET /auth/oauth/token/events** - Get token event history
- **GET /auth/oauth/jira/projects** - Get Jira projects using the OAuth token
- **GET /auth/oauth/jira/issues** - Get Jira issues using the OAuth token

## Usage

### Accessing the Dashboard

The token monitoring dashboard can be accessed at:
```
http://localhost:8000/dashboard/token
```

### API Usage

```python
# Get token status
GET /api/auth/oauth/token/status

# Force token refresh
POST /api/auth/oauth/token/refresh

# Get token events
GET /api/auth/oauth/token/events
```

## Configuration

The token service can be configured using environment variables:

- `JIRA_OAUTH_CLIENT_ID` - OAuth client ID
- `JIRA_OAUTH_CLIENT_SECRET` - OAuth client secret
- `TOKEN_FILE` - Path to token storage file (default: "oauth_token.json")

## Implementation Notes

### Background Thread Management

The background token refresh process runs in a separate thread to avoid blocking the main application. The thread:

1. Checks the token expiration periodically
2. Refreshes the token when it's nearing expiration
3. Implements proper error handling and retry logic
4. Uses thread synchronization to prevent race conditions

### Token Refresh Strategy

Tokens are refreshed under the following conditions:

1. **Pre-emptive refresh** - When a token is within the refresh threshold (default: 10 minutes) of expiration
2. **Force refresh** - When manually triggered through the API or dashboard
3. **On API call** - When token-dependent API calls are made and the token is near expiration

### Security Considerations

1. The token file is stored locally with appropriate file system permissions
2. Sensitive token data is masked in logs and API responses
3. Token refresh uses a secure TLS/HTTPS connection to the authorization server

## Troubleshooting

### Common Issues

1. **Token refresh failures** - Check network connectivity to the authorization server
2. **Background thread not running** - Check application logs for thread initialization errors
3. **Token expiration** - If a token expires, the dashboard will show "EXPIRED" status and trigger a refresh

### Logs

The token service logs events to the application log with the following levels:

- `INFO` - Normal operations (token refresh, thread start/stop)
- `WARNING` - Potential issues (token near expiration, retry attempts)
- `ERROR` - Critical issues (refresh failures, thread errors)
