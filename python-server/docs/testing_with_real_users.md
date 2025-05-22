# Testing with Real Jira Users

This guide explains how to test the multi-user authentication system with real Jira user accounts.

## Prerequisites

1. **Jira Admin Access**: You need admin access to create test user accounts in Jira
2. **Running Server**: The multi-user server should be running
3. **Test Accounts**: Create 2-3 test user accounts in your Jira instance
4. **OAuth App Configuration**: Make sure your Atlassian Developer Console OAuth app is configured with the correct callback URL: `http://localhost:8000/callback`

## Setup Steps

### 1. Verify OAuth Configuration

Before testing, ensure your environment variables are properly configured:

1. Check that the `.env` file contains:
   ```
   JIRA_OAUTH_CLIENT_ID=your-client-id-from-atlassian
   JIRA_OAUTH_CLIENT_SECRET=your-client-secret-from-atlassian
   JIRA_OAUTH_CALLBACK_URL=http://localhost:8000/callback
   ```

2. Make sure your OAuth app in Atlassian Developer Console is set up with:
   - The same client ID and secret
   - The exact callback URL: `http://localhost:8000/callback`
   - Appropriate scopes (read/write:jira-work)

### 2. Create Test Users in Jira

As a Jira admin, create test user accounts in your Jira instance:

1. Log into Jira as an administrator
2. Navigate to User Management (typically under Administration → User Management)
3. Create new test users with your own secure credentials:
   - User 1: [your-chosen-email-1] with a secure password
   - User 2: [your-chosen-email-2] with a secure password
   - User 3: [your-chosen-email-3] with a secure password
   
> **Important**: Use unique, valid email addresses that you have access to, and secure passwords following your organization's password policy. The example emails and passwords shown earlier were just placeholders.

Make sure these users have appropriate permissions to access the projects you want to test with.

### 3. Start the Server

Start the server with multi-user support:

```powershell
cd python-server
powershell -ExecutionPolicy Bypass -File .\start_multi_user_server.ps1
```

### 4. Run the Real Users Test Script

We have two options for testing with real users:

#### Option A: With Custom Credentials Entry (Recommended)

This script will ask for your Jira user details and guide you through the OAuth flow:

```powershell
cd python-server
python test_real_users_oauth_with_credentials.py
```

The script will:
1. Ask you to enter details about your Jira test accounts
2. Generate unique identifiers for each test
3. Open a browser to start the OAuth flow for each test user
4. Remind you which Jira account to use for each test
5. Verify that tokens are created and stored successfully
6. Test Jira API access with each authenticated user

#### Option B: Simple Testing Script

Alternatively, use the simpler script if you prefer to manage the accounts yourself:

```powershell
cd python-server
python test_real_users_oauth.py
```

With this script, you'll need to remember which Jira account to use for each test case.

## What This Tests

Testing with real users validates several important aspects:

1. **Complete OAuth Flow**: The full authentication flow from login to token creation
2. **Token Storage**: Proper storage and encryption of actual Jira OAuth tokens
3. **Multi-user Functionality**: The system's ability to handle different users simultaneously
4. **API Access**: Each user's ability to access Jira resources with their own permissions

## Troubleshooting

If you encounter issues:

1. **OAuth Errors**: Check that the OAuth app is correctly registered in Jira
2. **Redirect Issues**: Verify that the callback URL is correctly configured
3. **Permission Problems**: Ensure test users have the necessary permissions
4. **Token Storage**: Look for errors in the server logs related to token encryption or storage

## Next Steps After Testing

Once testing is successful:

1. Document the user IDs generated for each test account
2. Test the full extension functionality with these authenticated users
3. Verify that each user only sees their own data

For any questions or issues, please refer to the server logs or contact the development team.
