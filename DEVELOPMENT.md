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

2. **Python Server Issues**
   - Check if virtual environment is activated
   - Verify `.env` file has correct configuration
   - Ensure required ports are not already in use

3. **Edge Extension Issues**
   - Check browser console for JavaScript errors
   - Verify the extension is properly loaded in `edge://extensions/`
   - Ensure the manifest.json is valid
