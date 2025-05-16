# Python FastAPI Server for Jira Chatbot Edge Extension

This is the FastAPI backend server for the Jira Chatbot Edge Extension. It handles:
1. Natural language processing via OpenRouter API
2. Communication with the MCP-Atlassian server
3. Managing conversations and chat history
4. Scheduling and sending reminders

## Setup and Development

### Requirements

- Python 3.9+
- All dependencies listed in `requirements.txt`

### Getting Started

1. Create a virtual environment:
```
python -m venv venv
```

2. Activate the virtual environment:
```
# Windows
.\venv\Scripts\activate

# Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```
# Environment
ENVIRONMENT=development
DEBUG=True

# Server
HOST=0.0.0.0
PORT=8000

# MCP Server
MCP_SERVER_URL=http://localhost:9000/sse

# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key
```

5. Run the development server:
```
python run.py
```

Or directly with uvicorn:
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

When the server is running in development mode, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

- `app/` - Main application package
  - `main.py` - Application entry point
  - `api/` - API endpoints
    - `routes.py` - Main router
    - `endpoints/` - Endpoint modules
      - `chat.py` - Chat-related endpoints
      - `jira.py` - Jira-related endpoints
      - `health.py` - Health check endpoint
  - `core/` - Core application modules
    - `config.py` - Application configuration
  - `models/` - Data models
    - `chat.py` - Chat-related models
    - `jira.py` - Jira-related models
  - `services/` - Business logic services
    - `chat_service.py` - Chat processing service
    - `llm_service.py` - LLM integration service
    - `mcp_service.py` - MCP-Atlassian integration service
- `tests/` - Test modules
- `requirements.txt` - Project dependencies
- `run.py` - Script to run the server

## Testing

Run tests with pytest:
```
pytest
```

Or with coverage:
```
pytest --cov=app
```
