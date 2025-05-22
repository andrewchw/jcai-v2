# Multi-user Authentication for Jira Chatbot Extension

This document explains how to set up and use the multi-user authentication system for the Microsoft Edge Chatbot Extension for Jira Action Item Management.

## Overview

The multi-user authentication system allows multiple users to authenticate with Jira and use the extension independently. Each user's OAuth tokens are securely stored in a database with proper encryption.

## Features

- Support for multiple user accounts
- Secure token storage with encryption
- Database-backed persistence
- Migration tools from single-user to multi-user mode

## Setup Instructions

### 1. Set Up Environment

First, set up the multi-user environment:

```bash
python -m app.scripts.setup_multi_user
```

This script will:
- Create necessary directories
- Generate encryption keys
- Initialize the database

### 2. Migrate Existing Tokens (Optional)

If you have existing tokens from the previous single-user mode, you can migrate them:

```bash
python -m app.scripts.migrate_tokens
```

This will create a default user and associate the existing token with that user.

### 3. Configuration

You can configure the multi-user system using environment variables or a `.env` file:

```
# Multi-user settings
JIRA_ENABLE_MULTI_USER=true
JIRA_TOKEN_ENCRYPTION_KEY=your_encryption_key  # Will be auto-generated if not set
JIRA_DEFAULT_USER_EMAIL=default@example.com

# Database settings
DATABASE_URL=sqlite:///./data/tokens.db  # Default SQLite
# DATABASE_URL=postgresql://user:password@localhost/dbname  # PostgreSQL example
```

## API Endpoints

### Authentication Endpoints

- **Start OAuth Flow:** `/api/auth/oauth/v2/login?user_id=123`
- **OAuth Callback:** `/api/auth/oauth/v2/callback`
- **Get Token Status:** `/api/auth/oauth/v2/status?user_id=123`
- **Refresh Token:** `/api/auth/oauth/v2/refresh?user_id=123`
- **List Users:** `/api/auth/oauth/v2/users` (Admin only)

### Jira API Endpoints

- **Get Projects:** `/api/jira/v2/projects?user_id=123`
- **Get Issues:** `/api/jira/v2/issues?user_id=123&project_key=ABC`
- **Create Issue:** `/api/jira/v2/issues?user_id=123`

## Client Integration

To use multi-user authentication in the client:

1. Update API calls to include `user_id` parameter
2. Store user ID in client storage
3. If no user ID exists, generate one or use a default

Example client code:

```javascript
// Get user ID from storage or create one
const userId = localStorage.getItem('jira_user_id') || crypto.randomUUID();
localStorage.setItem('jira_user_id', userId);

// Use it in API calls
const response = await fetch(`/api/jira/v2/projects?user_id=${userId}`);
```

## Security Considerations

- Tokens are encrypted using Fernet symmetric encryption
- User IDs are UUIDs to prevent guessing
- Database access is limited to the application
- Token refreshes happen automatically

## Troubleshooting

If you encounter issues:

1. Check database connectivity: `sqlite3 data/tokens.db .tables`
2. Verify encryption key: `cat data/encryption_key.txt`
3. Check logs for error messages
4. Use the health endpoint: `/api/health?user_id=123`
