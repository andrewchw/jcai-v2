# JIRA Chatbot Assistant Edge Extension

This Microsoft Edge extension provides a chatbot interface for managing JIRA action items through natural language commands.

## Features

- Natural language interaction with JIRA
- Create, update, and track JIRA tasks
- View task status and details
- OAuth 2.0 authentication with JIRA Cloud
- Task notifications and reminders

## Development Setup

1. **Load the extension in Edge**:
   - Open Edge browser and navigate to `edge://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `edge-extension/src` folder

2. **Connect to Python backend**:
   - Ensure the Python FastAPI server is running on `http://localhost:8000`
   - The extension will automatically connect to the server

3. **Authentication**:
   - Click the login button in the extension's settings tab
   - Follow the OAuth flow to authenticate with your JIRA account

## Structure

- `manifest.json`: Extension configuration
- `html/sidebar.html`: Main UI layout
- `css/sidebar.css`: Styling for the sidebar
- `js/background.js`: Background service worker for API communication
- `js/sidebar.js`: UI interaction logic
- `js/content.js`: Content script for web page integration

## Building for Production

For production deployment, the extension should be packaged according to the Microsoft Edge Add-ons store requirements:

1. Replace placeholder icons with production-ready icons
2. Update the server URL in settings to point to the production server
3. Package the extension using the Edge Add-ons Developer Dashboard

## Testing

- **Authentication**: Test login and token refresh flow
- **Chat Interface**: Test message sending and receiving
- **Task Management**: Test creating and viewing tasks
- **Settings**: Test saving and loading user preferences

## Integration with Python Backend

The extension communicates with the Python FastAPI backend server which handles:

1. OAuth authentication with JIRA Cloud
2. Token management and refresh
3. JIRA API interactions
4. LLM processing for natural language understanding

API endpoints used:
- `/api/auth/jira/login`: Start OAuth flow
- `/api/auth/jira/token/status`: Check token status
- `/api/auth/jira/logout`: Invalidate token
- `/api/jira/projects`: Get JIRA projects
- `/api/jira/issues`: Get JIRA issues/tasks

## Future Enhancements

- Add support for file attachments
- Implement rich message formatting for chat responses
- Create context-aware suggestions based on current web page
- Add keyboard shortcuts for common actions
