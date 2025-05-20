from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import pathlib
from datetime import datetime
from datetime import datetime

from app.api.routes import api_router
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="Jira Chatbot API",
    description="API for Microsoft Edge Chatbot Extension for Jira",
    version="0.1.0",
)

# Set up static files serving from multiple possible locations
try:
    script_dir = pathlib.Path(__file__).parent.resolve()
    static_dir = script_dir / "static"
    
    if static_dir.exists():
        print(f"Mounting static files from: {static_dir}")
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    else:
        print(f"Static directory not found at: {static_dir}")
        # Try alternative locations
        alt_static_dir = pathlib.Path("app/static")
        if alt_static_dir.exists():
            print(f"Mounting static files from alternative path: {alt_static_dir}")
            app.mount("/static", StaticFiles(directory=str(alt_static_dir)), name="static")
except Exception as e:
    print(f"Error mounting static files: {e}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for the extension"""
    is_authenticated = False
    token_info = {"present": False}
    debug_info = {}
    
    try:
        from app.services.jira_service import jira_service
        if hasattr(jira_service, 'get_oauth2_token'):
            token = jira_service.get_oauth2_token()
            is_authenticated = token is not None
            token_info = {
                "present": token is not None,
                "type": "oauth2" if token else None
            }
            
            # Add debug logging
            try:
                from app.utils.auth_debug import log_token_details
                if token:
                    log_token_details(token, "health_check")
                    debug_info["token_checked"] = True
            except ImportError:
                print("Auth debug utilities not available")
                
    except Exception as e:
        print(f"Error checking auth status: {str(e)}")
        debug_info["error"] = str(e)
        
    return {
        "status": "ok",
        "authenticated": is_authenticated,
        "token_info": token_info,
        "debug": debug_info,
        "timestamp": datetime.now().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Jira Chatbot API",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "token_dashboard_url": "/dashboard/token"
    }

# Token dashboard endpoint
@app.get("/dashboard/token")
async def token_dashboard():
    static_dir = pathlib.Path(__file__).parent / "static"
    dashboard_file = static_dir / "token_dashboard.html"
    
    print(f"Attempting to serve dashboard file from: {dashboard_file}")
    print(f"File exists: {dashboard_file.exists()}")
    
    if not dashboard_file.exists():
        all_files = list(static_dir.glob("*")) if static_dir.exists() else []
        print(f"Files in static directory: {all_files}")
        return {"error": "Dashboard file not found", "path": str(dashboard_file), "static_dir_exists": static_dir.exists()}
        
    return FileResponse(dashboard_file)

# Alternative token dashboard endpoint with absolute path
@app.get("/dashboard/token2")
async def token_dashboard_alt():
    # Use an absolute path as a fallback
    script_dir = pathlib.Path(__file__).parent.resolve()
    project_root = script_dir.parent
    dashboard_file = project_root / "static" / "token_dashboard.html"
    
    # Try multiple possible locations
    possible_paths = [
        script_dir / "static" / "token_dashboard.html",
        project_root / "static" / "token_dashboard.html",
        project_root / "app" / "static" / "token_dashboard.html",
        pathlib.Path("app/static/token_dashboard.html"),
    ]
    
    for path in possible_paths:
        print(f"Checking path: {path}")
        if path.exists():
            print(f"Found dashboard at: {path}")
            return FileResponse(path)
    
    # If we can't find it, list all directories to help debug
    print("All paths failed, listing directories for debugging:")
    for path in [script_dir, project_root]:
        print(f"Contents of {path}:")
        for item in path.iterdir():
            print(f"  {item}")
    
    return {"error": "Dashboard file not found in any location"}
