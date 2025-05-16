# Microsoft Edge Chatbot Extension for Jira Action Item Management

This project implements a Microsoft Edge extension with a chatbot interface for managing Jira action items through natural language commands. The system automates task creation, reminders, and evidence tracking while maintaining firewall compliance.

## Project Components

- **Edge Extension:** Chromium-based sidebar UI for natural language task management
- **Python Server:** Backend for LLM processing and MCP server communication
- **MCP Server:** Docker-based server handling Jira Cloud interactions
- **Database:** SQLite for caching task data

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 18+
- Microsoft Edge browser (version 88+)

### Setup MCP-Atlassian Server

1. Clone this repository
2. Make sure your `mcp-atlassian.env` file is configured with the correct credentials
3. Start the MCP-Atlassian server using the provided script:

```powershell
.\start-mcp-server.ps1
```

For OAuth setup (if needed):

```powershell
.\setup-oauth.ps1
```

To verify the server is running:

```powershell
docker ps
```

The server will be available at:
- Standard mode: http://localhost:8080
- SSE mode (for streaming): http://localhost:9000/sse

### Setup Python FastAPI Server

1. Set up a virtual environment:

```powershell
cd python-server
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install the dependencies:

```powershell
pip install fastapi uvicorn aiohttp pydantic-settings
```

3. Start the server:

```powershell
cd python-server
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000, and the documentation at http://localhost:8000/docs

### Setup Edge Extension

1. Open Microsoft Edge
2. Go to `edge://extensions/`
3. Enable "Developer mode" in the bottom-left corner
4. Click "Load unpacked" and select the `edge-extension/src` folder
5. The extension should now be loaded and active

## Current Status

According to the Project Management Plan, we're currently in Phase 1 (Core Features) which runs from May 14 to June 4, 2025.

### Completed (as of May 16, 2025):
- Initial project requirements gathering
- Creation of PRD, SRS, and UI documentation
- Setup of development environment
- Repository structure definition and creation
- Configuration of environment files for MCP-Atlassian server
- Initial setup of OAuth credentials for Jira Cloud integration
- Docker environment configuration with scripts for easy management
- Basic project structure for both the Edge extension and Python server
- Edge extension scaffold with sidebar UI
- Python server foundation with API endpoints

### In Progress:
- Testing MCP-Atlassian server connectivity to Jira Cloud
- Implementing OAuth flow in the Edge extension
- Developing the Python server's LLM integration
- Connecting the Edge extension to the Python server

## Testing the Setup

### 1. Test MCP-Atlassian Server Connection

Before proceeding with development, ensure the MCP-Atlassian server can connect to Jira Cloud:

```powershell
# Start the MCP-Atlassian server in SSE mode
.\start-mcp-server.ps1

# In another terminal, run the connection test
cd python-server
python test_mcp_connection.py
```

### 2. Verify OAuth Setup

If you're using OAuth for authentication (recommended):

```powershell
# Complete OAuth setup if not done already
.\setup-oauth.ps1

# Check OAuth status
cd python-server
python check_oauth.py
```

## Next Steps and Development Tasks

### Edge Extension Development
1. Design and implement login/authentication UI
2. Create proper chat interaction flow
3. Add icons and improve styling
4. Implement notification system for reminders

### Python Server Development
1. Complete MCP-Atlassian integration
2. Implement OpenRouter LLM service
3. Create SQLite database for caching
4. Develop natural language processing for Jira commands

### Integration
1. Connect Edge extension to Python server API
2. Test end-to-end communication flow
3. Implement error handling and retry logic

## Project Documentation

For more details, refer to the documentation in the `documentation` folder:
- PRD (Product Requirements Document)
- SRS (Software Requirements Specification)
- UI Description Document
- Project Management Plan
