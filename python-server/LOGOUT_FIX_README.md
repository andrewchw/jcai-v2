# Fixing the Logout Functionality

This document provides instructions on how to fix the "stopTokenChecking is not defined" error that occurs when clicking the Logout button in the JIRA Chatbot Extension.

## The Problem

When clicking the "Logout" button in the extension, the following error occurs:

```
Error handling sidebar message: ReferenceError: stopTokenChecking is not defined
```

Additionally, the server logs show HTTP 405 Method Not Allowed errors:

```
INFO: 127.0.0.1:56192 - "POST /api/auth/oauth/v2/logout?user_id=edge-1747957230093-kh1ir7hn HTTP/1.1" 405 Method Not Allowed
```

## Root Causes

1. **Missing Function**: The `stopTokenChecking` function is called in `performLogout()`, but it's not defined anywhere in the background.js file.
2. **HTTP Method Mismatch**: The client is using POST requests, but the server only accepts GET requests for the logout endpoint.

## Solutions

### 1. Client-Side Fix (Background.js)

Add the missing `stopTokenChecking` function to the background.js file before the `performLogout` function (around line 700):

```javascript
/**
 * Stop periodic token checking
 */
function stopTokenChecking() {
    console.log('Stopping periodic token checking');
    if (self.tokenCheckIntervalId) {
        clearInterval(self.tokenCheckIntervalId);
        self.tokenCheckIntervalId = null;
    }
}
```

### 2. Server-Side Fix (OAuth Endpoint)

Add a POST method endpoint for logout in the `app/api/endpoints/oauth_multi.py` file after the existing GET endpoint:

```python
@router.post("/logout")
async def logout_post(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Logout and invalidate OAuth token for a user via POST request"""
    # This simply calls the same implementation as the GET endpoint
    return await logout(user_id=user_id, db=db)
```

### 3. Alternative Client-Side Fix

If you can't modify the server to accept POST requests, update the client to use GET instead. In the `performLogout` function, change:

```javascript
await fetch(`${API_BASE_URL}/auth/oauth/v2/logout?user_id=${encodeURIComponent(tokenState.userId)}`, {
    method: 'POST', // Or GET, depending on your API
});
```

To:

```javascript
await fetch(`${API_BASE_URL}/auth/oauth/v2/logout?user_id=${encodeURIComponent(tokenState.userId)}`, {
    method: 'GET'
});
```

## Applying the Fixes

### Automated Method

1. Run the PowerShell script to apply the server-side fix:
   ```powershell
   .\apply_logout_fix.ps1
   ```

2. This will add the POST endpoint to the server. Follow the instructions for manually adding the `stopTokenChecking` function to your background.js file.

### Manual Method

1. Review the detailed instructions in `fix_logout_functionality.py`:
   ```bash
   python fix_logout_functionality.py
   ```

2. Apply the fixes as described in the instructions.

## Verifying the Fix

1. Restart your server after making the changes
2. Reload your browser extension
3. Test the logout functionality to confirm it works without errors

## Related Utility Scripts

- `cleanup_specific_token.py`: Manually delete a token for a specific user ID
- `python_logout_handler.py`: A standalone script for handling the logout process

## Troubleshooting

If you're still experiencing issues after applying these fixes:

1. Check your browser console for errors
2. Look at the server logs for any error messages
3. Verify that the correct user ID is being passed to the logout endpoint
4. Try manually deleting the problematic token using `cleanup_specific_token.py`
