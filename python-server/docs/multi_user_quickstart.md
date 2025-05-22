# Multi-user Authentication for Jira Chatbot Extension

## Quick Start Guide

Follow these steps to enable multi-user authentication for the Microsoft Edge Chatbot Extension for Jira Action Item Management:

### Server Setup

1. **Start the server with multi-user support:**

```powershell
cd python-server
.\start_multi_user_server.ps1
```

This script will:
- Create the necessary data directory
- Initialize the database
- Set up encryption keys
- Start the server with multi-user support enabled

2. **Verify that multi-user support is working:**

```
GET /api/health
```

The response should include:
```json
{
  "status": "ok",
  "multi_user_enabled": true,
  ...
}
```

### Testing Multi-user Support

1. **Create a test user and token:**

```powershell
cd python-server
python test_multi_user.py
```

This will create a test user and token, and print instructions for testing the APIs.

2. **Use the generated user ID to test endpoints:**

```
GET /api/health?user_id=<user_id>
GET /api/auth/oauth/v2/status?user_id=<user_id>
GET /api/jira/v2/projects?user_id=<user_id>
```

### Client Integration

1. Update your browser extension to include the `multi_user_migration.js` script.
2. Use the client-side migration helper:

```javascript
// Initialize migration helper
const migrationHelper = new MultiUserMigration();

// Ensure a user ID exists
const userId = migrationHelper.ensureUserId();

// Update API endpoints to include user ID
const updatedApi = migrationHelper.updateApiEndpoints(api);

// Use the updated API for all requests
updatedApi.jira.getProjects().then(projects => {
  // Handle projects
});
```

## Endpoint Reference

### Authentication Endpoints

| Endpoint | Description | Query Parameters |
|----------|-------------|-----------------|
| `GET /api/auth/oauth/v2/login` | Start OAuth flow | `user_id` (optional) |
| `GET /api/auth/oauth/v2/callback` | OAuth callback | `state` (contains user_id) |
| `GET /api/auth/oauth/v2/status` | Check token status | `user_id` (required) |
| `POST /api/auth/oauth/v2/refresh` | Refresh token | `user_id` (required) |

### Jira API Endpoints

| Endpoint | Description | Query Parameters |
|----------|-------------|-----------------|
| `GET /api/jira/v2/projects` | List projects | `user_id` (required) |
| `GET /api/jira/v2/issues` | List issues | `user_id` (required), `project_key` (optional) |
| `POST /api/jira/v2/issues` | Create issue | `user_id` (required) |

## Migration from Single-user Mode

To migrate from single-user mode to multi-user mode:

1. Run the migration script:

```powershell
cd python-server
python -m app.scripts.migrate_tokens
```

2. This will create a default user and associate existing tokens with that user.
3. Update your client code to include user IDs in API calls.

## Troubleshooting

- **Database Issues**: Check the database file at `python-server/data/tokens.db`
- **Token Encryption**: If you see encryption errors, delete the encryption key and let it regenerate
- **Authentication Failures**: Verify that the user ID is being correctly passed in API calls
