# Microsoft Edge Chatbot Extension for Jira

This folder contains the Microsoft Edge extension that provides a sidebar interface for natural language interaction with Jira.

## Features

- Sidebar UI for chatting with the AI assistant
- Create, update, and query Jira issues through natural language
- File upload for evidence attachment
- Reminder notifications for upcoming due dates

## Development Setup

1. Open Edge browser and navigate to `edge://extensions/`
2. Enable "Developer mode" in the bottom-left corner
3. Click "Load unpacked" and select this directory
4. The extension should appear in your extensions list

## Project Structure

- `src/` - Source code
  - `manifest.json` - Extension manifest
  - `html/` - HTML files
    - `sidebar.html` - Sidebar UI
  - `css/` - Stylesheets
    - `sidebar.css` - Sidebar styling
  - `js/` - JavaScript files
    - `background.js` - Background service worker
    - `sidebar.js` - Sidebar functionality
  - `icons/` - Extension icons

## Building for Production

To package the extension for production:

1. Ensure all files are in the `src/` directory
2. Compress the `src/` directory into a ZIP file
3. The ZIP can be manually installed in Edge or submitted to the Edge Add-ons Store

## Configuration

The extension communicates with the Python server running on `http://localhost:8000`. To change this:

1. Update the `host_permissions` in `manifest.json`
2. Update the API endpoint in `sidebar.js`
