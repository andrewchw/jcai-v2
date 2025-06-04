# Configuring Atlassian OAuth 2.0 for Refresh Tokens

This guide explains how to configure your Atlassian application to issue refresh tokens, allowing for automatic token renewal without requiring user re-authentication.

## Understanding Atlassian OAuth 2.0 Refresh Tokens

Atlassian's OAuth 2.0 implementation requires the `offline_access` scope to enable refresh tokens.

### Key Points
- Refresh tokens require the `offline_access` scope in your authorization request
- Your application must be configured to use the `authorization_code` grant type
- The refresh token allows your application to obtain new access tokens without user interaction

## Step-by-Step Configuration

Follow these steps to enable refresh tokens for your Atlassian OAuth application:

### 1. Access the Atlassian Developer Console
- Go to https://developer.atlassian.com/console/myapps/
- Log in with your Atlassian account
- Select your OAuth 2.0 application

### 2. Navigate to Authorization Settings
- Look for the "Authorization" or "OAuth 2.0" section
- Find settings related to token issuance

### 3. Enable Refresh Tokens
- Look for an option labeled "Refresh Token" or "Issue refresh tokens"
- Enable this option
- Save your changes

### 4. Update Scopes (if necessary)
- Make sure your application has the necessary scopes:
  - `read:jira-user`
  - `read:jira-work`
  - `write:jira-work`
  - Any other scopes your application needs

### 5. Re-authorize your application
- After making these changes, users need to re-authorize your application
- Execute the OAuth flow again:
  ```powershell
  python logout_oauth_token.py   # Delete the existing token
  python jira_oauth2_example.py  # Start the OAuth server
  ```
- Navigate to http://localhost:8000/login to begin authentication
- Verify that a refresh token was issued:
  ```powershell
  python check_oauth_token.py
  ```

## Handling Refresh Tokens in Code

Once you have a refresh token, your code needs to:

1. **Store the refresh token securely** - Refresh tokens are long-lived and must be protected
2. **Detect token expiration** - Check if the access token is expired or about to expire
3. **Refresh automatically** - Use the refresh token to obtain a new access token when needed

### Example Refresh Logic

```python
def refresh_token(token):
    """Refresh the OAuth 2.0 token if it's expired"""
    try:
        # Create a new OAuth2 session
        oauth = OAuth2Session(CLIENT_ID, token=token)

        # Check if token is expired or about to expire (within 60 seconds)
        if 'expires_at' in token:
            expires_at = token['expires_at']
            if datetime.now().timestamp() > (expires_at - 60):
                logger.info("Token is expired or about to expire, refreshing...")

                # Refresh the token
                new_token = oauth.refresh_token(
                    TOKEN_URL,
                    refresh_token=token['refresh_token'],
                    client_id=CLIENT_ID,
                    client_secret=CLIENT_SECRET
                )

                # Save the new token
                save_token(new_token)
                return new_token

        return token
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return None
```

## Troubleshooting

If you're still not getting refresh tokens after these steps:

1. **Check Application Type**: Ensure your app is registered as a "3LO" (3-legged OAuth) application
2. **Verify Grant Type**: Make sure your app is using the `authorization_code` grant type
3. **Try Client Credentials**: Some Atlassian apps may require client credentials to be passed in the token request
4. **Check Documentation**: Refer to the [Atlassian OAuth 2.0 (3LO) documentation](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
5. **Contact Support**: If all else fails, contact Atlassian developer support

## Resources

- [Atlassian OAuth 2.0 (3LO) Documentation](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)
