# Development Guide: Microsoft Edge Chatbot Extension for Jira

This guide provides detailed instructions for developers working on the Microsoft Edge Chatbot Extension for Jira Action Item Management project.

## Project Overview

We're building a Microsoft Edge extension with a chatbot interface for managing Jira action items using natural language. The system consists of:

1. **Edge Extension**: The frontend UI that users interact with
2. **Python FastAPI Server**: The backend that processes user requests and communicates with both the LLM and Jira
3. **MCP-Atlassian Server**: A Docker-based server that abstracts Jira API complexities
4. **SQLite Database**: Local storage for caching data

## Development Environment Setup

### Prerequisites

- Git
- Docker Desktop
- Python 3.9+
- Node.js 18+ (for extension development)
- VS Code (recommended)
- Microsoft Edge (version 88+)

### Initial Setup

1. **Clone the repository**:
   ```powershell
   git clone <repository-url>
   cd jcai-v2
   ```

2. **Configure MCP-Atlassian server**:
   - Ensure `mcp-atlassian.env` is properly configured with Jira credentials
   - Run OAuth setup if using OAuth authentication:
     ```powershell
     .\setup-oauth.ps1
     ```

3. **Set up Python server**:
   ```powershell
   cd python-server
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Load Edge extension for development**:
   - Open Edge browser and navigate to `edge://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select `edge-extension/src` folder

## Running the Application

1. **Start MCP-Atlassian server**:
   ```powershell
   .\start-mcp-server.ps1
   ```
   Choose "Y" when prompted about SSE mode.

2. **Start Python FastAPI server**:
   ```powershell
   cd python-server
   .\venv\Scripts\Activate.ps1
   python run.py
   ```
   The API will be available at `http://localhost:8000/docs`

3. **Test the Edge extension**:
   The extension should be available in your Edge browser. Click the extension icon to open the sidebar.

## Development Workflow

### MCP-Atlassian Server Development

- The MCP-Atlassian server is a pre-built Docker container, so you don't need to modify it
- To check if it's working correctly, run:
  ```powershell
  cd python-server
  python test_mcp_connection.py
  ```
- To verify OAuth status:
  ```powershell
  cd python-server
  python check_oauth.py
  ```
- For SSE communication, the server needs to be started with:
  ```powershell
  .\start-mcp-server.ps1
  # Choose "Y" when prompted about SSE mode
  ```
- MCP server endpoints:
  - Standard mode: http://localhost:8080
  - SSE mode (for Python server): http://localhost:9000/sse
  - Invoke endpoint for tools: http://localhost:9000/sse/invoke

### Python Server Development

1. **API Endpoints**
   - Add new endpoints in `python-server/app/api/endpoints/`
   - Register them in `python-server/app/api/routes.py`

2. **Services**
   - Business logic should be in `python-server/app/services/`
   - `mcp_service.py`: Handles communication with MCP-Atlassian server
   - `llm_service.py`: Handles communication with OpenRouter LLM
   - `chat_service.py`: Processes chat messages and orchestrates responses

3. **Data Models**
   - Define Pydantic models in `python-server/app/models/`

### Edge Extension Development

1. **UI Components**
   - HTML templates in `edge-extension/src/html/`
   - CSS styles in `edge-extension/src/css/`

2. **JavaScript Logic**
   - Background script in `edge-extension/src/js/background.js`
   - Sidebar UI logic in `edge-extension/src/js/sidebar.js`

3. **Extension Configuration**
   - Manifest in `edge-extension/src/manifest.json`

## Coding Standards

1. **Python Code**
   - Follow PEP 8 style guide
   - Use async/await for asynchronous operations
   - Document functions with docstrings

2. **JavaScript Code**
   - Use ES6+ features
   - Follow camelCase naming convention
   - Comment complex logic

3. **CSS**
   - Use BEM naming convention
   - Keep styles modular and reusable

## Testing

1. **Component Testing**
   - MCP-Atlassian server: Use the provided test scripts
     ```powershell
     # Test basic connectivity
     python python-server/test_mcp_connection.py
     
     # Test OAuth configuration
     python python-server/check_oauth.py
     ```
   - Python server: Run unit tests
     ```powershell
     cd python-server
     python -m pytest tests/
     ```
   - Edge extension: Use the browser's developer tools (F12) to debug

2. **Manual Testing**
   - Test all features on Microsoft Edge latest version
   - Verify both online and offline behavior
   - Check responsive design for various sidebar widths
   - Test natural language commands for different Jira operations

3. **Integration Testing**
   - Verify end-to-end flow from UI to LLM to Jira and back
   - Test error handling when services are unavailable
   - Check authentication token refresh mechanisms

## Deployment

### Development Deployment

- The extension can be loaded as an unpacked extension in Edge
- The Python server runs locally on your machine
- The MCP-Atlassian server runs in Docker

### Production Deployment

- Package the Edge extension for the Microsoft Store
- Deploy the Python server to a company intranet server
- Set up the MCP-Atlassian server as a Docker container on the intranet

## Troubleshooting

### Common Issues

1. **MCP-Atlassian Server Connection Problems**
   - Check that Docker is running
   - Verify the Jira credentials in `mcp-atlassian.env`
   - Ensure OAuth setup has been completed if using OAuth
   - Check that no other services are using ports 8080 or 9000
   - Verify Docker network connectivity with `docker network inspect bridge`
   - If SSE mode is required, ensure the `--transport sse --port 9000` flags are used

2. **OAuth Connection Issues**
   - Verify your Jira Cloud instance is properly configured for OAuth
   - Check that the OAuth credentials in `mcp-atlassian.env` match your Jira app settings
   - Make sure the redirect URL is properly set
   - Clear browser cookies and try the OAuth flow again
   - Run `check_oauth.py` to diagnose specific OAuth issues

3. **Python Server Issues**
   - Check if virtual environment is activated
   - Verify `.env` file has correct configuration
   - Ensure required ports are not already in use
   - Check for Python dependency issues with `pip list`
   - Look for error logs in the console output
   - Verify the OpenRouter API key is valid

4. **Edge Extension Issues**
   - Check browser console for JavaScript errors (press F12)
   - Verify the extension is properly loaded in `edge://extensions/`
   - Ensure the `manifest.json` is valid
   - Check that content security policies aren't blocking connections
   - Clear extension storage with `localStorage.clear()` in the console
   - Try reloading the extension

### Debugging Tools

1. **Docker Debugging**
   ```powershell
   # Check Docker container status
   docker ps
   
   # View container logs
   docker logs <container-id>
   
   # Check container network
   docker network inspect bridge
   ```

2. **Python Server Debugging**
   ```powershell
   # Run the server in debug mode
   cd python-server
   python run.py --debug
   
   # Check API endpoints
   curl http://localhost:8000/health
   ```

3. **API Testing**
   - Use the Swagger UI at `http://localhost:8000/docs`
   - Test endpoints directly with curl or Postman
   - Monitor network requests in the browser developer tools

## Connection Testing

This section provides guidance on verifying the connections between the various components of the system.

### MCP-Atlassian to Jira Cloud Connection

1. **Basic Connectivity Test**
   ```powershell
   cd python-server
   python test_mcp_connection.py
   ```
   This script attempts to fetch projects from Jira via the MCP server.

2. **OAuth Verification**
   ```powershell
   cd python-server
   python check_oauth.py
   ```
   This script verifies that OAuth authentication is working properly by fetching the current user.

### Python Server to MCP-Atlassian Connection

1. **Start the Python server and check the logs**
   ```powershell
   cd python-server
   .\venv\Scripts\Activate.ps1
   python run.py
   ```

2. **Make a test request to trigger MCP communication**
   ```powershell
   curl http://localhost:8000/api/jira/projects
   ```
   This endpoint should communicate with the MCP server to fetch projects.

### Edge Extension to Python Server Connection

1. **Load the extension and open the console**
   - Navigate to `edge://extensions/`
   - Click on "background page" for the extension
   - Open the Console tab

2. **Send a test message from the extension**
   - Click on the extension icon to open the sidebar
   - Enter a test message like "Hello"
   - Check the network tab in Developer Tools to verify the request to the Python server

3. **Manually test the API connection**
   ```javascript
   // Run this in the browser console
   fetch('http://localhost:8000/api/chat/message', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       message: 'Test message',
       conversation_id: null
     })
   }).then(response => response.json()).then(console.log)
   ```

### End-to-End Integration Test

To verify that all components can communicate with each other:

1. Start the MCP-Atlassian server in SSE mode
2. Start the Python FastAPI server
3. Load the Edge extension
4. Send a Jira-related query from the extension (e.g., "Show my Jira tasks")
5. Verify that:
   - The request reaches the Python server (check logs)
   - The Python server forwards the request to the OpenRouter API
   - The Python server communicates with the MCP server
   - The MCP server fetches data from Jira
   - The response flows back to the Edge extension UI

This end-to-end test verifies that all components are properly connected and can communicate with each other.

## Security Considerations
