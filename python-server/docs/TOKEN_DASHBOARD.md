# OAuth Token Monitoring Dashboard

## Overview

The OAuth Token Monitoring Dashboard provides a web interface for monitoring the status of OAuth tokens and testing Jira API connectivity. This dashboard helps administrators ensure that OAuth tokens are being properly managed and refreshed, and that they can successfully connect to Jira Cloud.

## Features

### Token Status Monitoring

- Real-time display of token status (active, expired, refreshing, error)
- Countdown timer to token expiration
- Timestamp for last refresh and next scheduled check
- Refresh statistics (attempts, successes, failures)

### Token Management

- Manual token refresh capability
- Token event history viewer
- Visual indicators for token health

### Jira Integration Testing

- Jira project listing functionality
- Jira issue retrieval and display
- Visual project selection interface
- Issue status indicators with color coding

## Accessing the Dashboard

The token monitoring dashboard can be accessed at:
```
http://localhost:8000/dashboard/token
```

## Dashboard Sections

### 1. Token Status

This section displays the current status of the OAuth token, including:

- Active/expired status
- Countdown to expiration
- Last refresh time
- Next scheduled check

### 2. Token Stats

This section shows statistics about token refresh operations:

- Refreshes attempted
- Refreshes succeeded
- Refreshes failed

### 3. Token Event History

This section displays a chronological list of token-related events:

- Refresh events (successful token refreshes)
- Error events (failed refresh attempts)
- Warning events (potential issues)
- Info events (general information)

### 4. Jira Integration Test

This section demonstrates that the OAuth token is working correctly by connecting to Jira Cloud and retrieving data:

#### Projects Tab
- Fetches and displays all accessible Jira projects
- Clicking on a project card will automatically:
  - Switch to the Issues tab
  - Select that project
  - Load issues for that project

#### Issues Tab
- Displays issues from a selected project
- Shows key information like summary, status, assignee, and update time
- Color-coded status indicators for better visualization

## Usage

### Token Management

1. **Viewing Token Status**: The token status is displayed at the top of the dashboard with a countdown timer.

2. **Manual Token Refresh**: Click the "Force Token Refresh" button to manually trigger a token refresh operation.

3. **Monitoring Events**: The event history section shows a log of all token-related events.

### Jira Integration Testing

1. **Loading Projects**:
   - Click the "Load Jira Projects" button in the Projects tab
   - A grid of project cards will be displayed

2. **Loading Issues**:
   - Select a project from the dropdown in the Issues tab
   - Click "Load Issues" to retrieve and display issues from that project
   - Alternatively, click on a project card in the Projects tab

## Troubleshooting

### Common Issues

1. **"Not connected to Jira"**: Check that your OAuth token is valid and not expired. Try clicking "Force Token Refresh" to refresh the token.

2. **No projects displayed**: Verify that your OAuth token has the necessary permissions to access Jira projects.

3. **Issues not loading**: Ensure that the selected project exists and that your OAuth token has permissions to view issues in that project.

### Error Messages

Error messages are displayed in red text. Common errors include:

- Token refresh failures
- Connection errors to Jira Cloud
- Permission errors when accessing projects or issues

## Security Considerations

- The dashboard does not display sensitive token information (tokens are masked)
- API calls are made server-side, not from the browser
- All communication with Jira Cloud is secured using HTTPS
