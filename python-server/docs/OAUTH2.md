# Jira OAuth 2.0 Implementation

This document explains the implementation of OAuth 2.0 for Atlassian Jira in the Microsoft Edge Chatbot Extension project.

## Overview

Atlassian Jira Cloud uses OAuth 2.0 for secure API access. Our implementation follows the Authorization Code Grant flow, which is the recommended approach for server-side applications.

### Key Components

1. **OAuth 2.0 Flow**: Complete authorization code flow with token refreshing capabilities
2. **Token Storage**: Secure storage and management of access and refresh tokens
3. **API Integration**: Seamless integration with Atlassian Python API using OAuth tokens
4. **Error Handling**: Comprehensive error handling for OAuth and API operations

## Implementation Details

### OAuth 2.0 Flow

The OAuth 2.0 flow consists of the following steps:

1. **Authorization Request** (User redirected to Atlassian)
   - Redirect users to Atlassian's authorization page
   - Request necessary scopes for Jira API access
   - Include state parameter for CSRF protection

2. **Authorization Grant** (Callback from Atlassian)
   - Process authorization code from callback
   - Exchange code for access and refresh tokens
   - Store tokens securely

3. **API Access** (Using obtained tokens)
   - Use access token to make API requests
   - Automatically refresh tokens when they expire
   - Handle token revocation and errors

### Scopes

Our implementation requests the following scopes:

- `read:jira-user`: Read user information
- `read:jira-work`: Read issues, boards, and other work data
- `write:jira-work`: Create and update issues, comments, and work items
- `manage:jira-project`: Manage project settings (optional)
- `manage:jira-configuration`: Manage Jira configuration (optional)

### Token Storage

Tokens are stored securely and include:

- Access token
- Refresh token
- Token type
- Expiration time
- Scope information

## Endpoints

The following endpoints are implemented for the OAuth 2.0 flow:

- `/api/auth/jira/login`: Initiates OAuth flow (redirects to Atlassian)
- `/api/auth/jira/callback`: Handles OAuth callback from Atlassian
- `/api/auth/jira/refresh`: Refreshes OAuth token
- `/api/auth/jira/logout`: Revokes token and logs out user

## How to Use

### Setup in Atlassian Developer Console

1. Create a new OAuth 2.0 integration in the [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Configure callback URL to match your application's URL
3. Request the necessary scopes
4. Note your Client ID and Client Secret

### Configure Environment Variables

Set the following environment variables:

```
JIRA_OAUTH_CLIENT_ID=your_client_id
JIRA_OAUTH_CLIENT_SECRET=your_client_secret
JIRA_OAUTH_CALLBACK_URL=https://your-server/api/auth/jira/callback
```

### Example Code

```python
from app.services.jira_service import jira_service

# Set OAuth token after obtaining it
token_data = {
    "access_token": "obtained_access_token",
    "token_type": "Bearer",
    "refresh_token": "obtained_refresh_token",
    "expires_in": 3600
}
jira_service.set_oauth2_token(token_data)

# Now you can use the Jira service with OAuth authentication
projects = jira_service.get_projects()
```

## Testing

You can test the OAuth 2.0 implementation by running the provided example script:

```bash
python jira_oauth2_example.py
```

This will start a local server that demonstrates the complete OAuth flow.

## Troubleshooting

Common issues and solutions:

1. **Invalid redirect_uri**: Ensure the callback URL configured in the Atlassian Developer Console exactly matches the one used in your application.

2. **Token expiration**: The access token expires after a set period (typically 1 hour). Our implementation automatically refreshes tokens using the refresh token.

3. **Insufficient scopes**: If you encounter permission errors, check that you've requested all necessary scopes in the authorization request.

4. **Invalid client credentials**: Verify that your client ID and client secret are correct.

## References

- [Atlassian OAuth 2.0 (3LO) Documentation](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
- [Atlassian Python API Documentation](https://atlassian-python-api.readthedocs.io/en/latest/jira.html)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)
