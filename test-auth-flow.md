# Authentication Flow Test Plan

## Setup
1. Start the Python server: Run `restart_server.ps1` or start manually
2. Load the Edge extension: Navigate to edge://extensions/ and reload the extension

## Test Cases

### 1. Initial State Check
- [ ] Open the extension sidebar
- [ ] Verify "Not authenticated" status is shown
- [ ] Verify "Login to Jira" button is enabled
- [ ] Verify "Logout" button is disabled
- [ ] Verify server connection status shows "Connected" if server is running

### 2. Authentication Flow
- [ ] Click "Login to Jira" button
- [ ] Complete Jira OAuth authentication in the opened tab
- [ ] Verify tab closes automatically after successful auth
- [ ] Verify extension status changes to "Authenticated"
- [ ] Verify "Login to Jira" button becomes disabled
- [ ] Verify "Logout" button becomes enabled

### 3. Persistence Testing
- [ ] Close and reopen the sidebar
- [ ] Verify authentication state persists (should still show "Authenticated")
- [ ] Verify "Login to Jira" button remains disabled
- [ ] Verify "Logout" button remains enabled

### 4. Server Connectivity
- [ ] If server disconnects, verify status shows "Connection failed"
- [ ] Restart server and verify status updates to "Connected"
- [ ] Verify authentication state remains intact after server reconnection

### 5. Logout Flow
- [ ] Click "Logout" button
- [ ] Verify status changes to "Not authenticated"
- [ ] Verify "Login to Jira" button becomes enabled again
- [ ] Verify "Logout" button becomes disabled

## Debug Tools

### New Debugging Utilities
The following debug tools have been added to help troubleshoot authentication issues:

1. **auth_debug.py**: Added to `python-server/app/utils/`
   - Provides functions to log token details
   - Creates token backups
   - Adds detailed logging for auth operations

2. **Enhanced Health Check API**:
   - Now includes token information
   - Logs authentication status
   - Provides debug information

3. **test_auth_flow.ps1**:
   - Script to restart server and test authentication flow
   - Option to clean old tokens (`-clean` parameter)
   - Opens health endpoint automatically

### Steps to Use Debug Tools:

1. **Server Logs**:
   - Check `oauth_debug.log` in the server directory
   - Contains detailed info about token state and auth operations

2. **Browser Console**:
   - Enhanced logging in both sidebar.js and background.js
   - Shows authentication events and token status

3. **Health Check Endpoint**:
   - Visit http://localhost:8000/api/health to see current auth status
   - Provides token presence and timestamp information
