# How to Fix "Invalid Token" When OAuth is Valid but Jira API Fails

This document explains how to address an issue where the OAuth token status shows as valid, but the Jira API calls (projects and issues) fail with 500 errors.

## Problem Diagnosis

Based on server logs and extension behavior:

1. The OAuth authentication flow is working correctly
2. Token status checks return 200 OK with a valid token
3. Jira API calls fail with 500 Internal Server Error
4. Extension UI shows "Invalid token" despite successful authentication

## Problem Root Cause

This issue occurs when there is a mismatch between the OAuth authentication and the Jira API integration. The most common causes are:

1. The OAuth token does not have the required Jira API scopes (missing permissions)
2. The Jira API integration is not properly configured on the server
3. The Jira account associated with the token doesn't have access to the requested projects
4. Network issues between the server and Jira's API

## Solution: Backend Fixes

1. **Check Jira API configuration**:
   ```powershell
   cd python-server
   python test_jira_connection.py
   ```

2. **Verify OAuth token has correct scopes**:
   The OAuth token should include: `read:jira-user read:jira-work write:jira-work offline_access`

3. **Regenerate OAuth token with correct scopes**:
   Run the OAuth troubleshooter to create a new token with the right permissions:
   ```powershell
   python python-server/jira_oauth2_troubleshooter.py
   ```

## Solution: Frontend (Extension) Fixes

Since the OAuth token checks are passing but Jira API calls are failing, the extension should:

1. Update the UI to show "Connected to server, but Jira API access failed" instead of "Invalid token"
2. Better distinguish between authentication failures and Jira API failures
3. Display specific error messages from the server to help users understand the issue

The changes to the Edge extension code we've made accomplish this by:

1. Enhancing error handling in the Jira API fetch functions
2. Extracting more detailed error information from API responses
3. Separating authentication status from Jira API access status
4. Displaying clearer error messages to users

## Testing the Fix

1. Run the diagnostic script to verify the exact issue:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\diagnose_jira_connection.ps1
   ```

2. Check the OAuth token status and Jira API status separately
3. Verify the UI shows the correct status for both OAuth and Jira API access

## Prevention

To prevent this issue in the future:
1. Add more detailed server logging for Jira API failures
2. Implement routine token validation that checks both authentication and API access
3. Create automated tests that verify complete Jira integration, not just authentication
