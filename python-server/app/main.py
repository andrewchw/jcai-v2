import os
import pathlib
from datetime import datetime
from typing import Any, Dict, Optional

from app.api.endpoints.oauth_multi import callback as oauth_multi_callback
from app.api.routes import api_router
from app.core.config import settings
from app.core.database import get_db
from app.core.init_db import init_db
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Create FastAPI app
app = FastAPI(
    title="Jira Chatbot API",
    description="API for Microsoft Edge Chatbot Extension for Jira",
    version="0.2.0",
)

# Add direct route for OAuth callback to match Atlassian Developer Console configuration


@app.get("/callback")
async def root_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    setup_example: bool = False,
    success: bool = False,
    db: Session = Depends(get_db),  # Add database session
):
    """
    Root level OAuth callback that matches the callback URL registered in Atlassian Developer Console
    """
    # Extract user_id from state parameter (format: "user_id:abc123")
    user_id = None
    if state and state.startswith("user_id:"):
        user_id = state.split("user_id:")[1]

    # Log the callback details
    print(
        f"OAuth callback received at root level: state={state}, code={'present' if code else 'missing'}, user_id={user_id}"
    )

    # Forward to the actual callback handler in oauth_multi with the extracted parameters and db session
    return await oauth_multi_callback(
        request=request,
        user_id=user_id,
        code=code,
        state=state,
        setup_example=setup_example,
        success=success,
        db=db,
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
            app.mount(
                "/static", StaticFiles(directory=str(alt_static_dir)), name="static"
            )
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


# Startup event handler to initialize the database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    import logging

    logger = logging.getLogger("app.startup")
    logger.info("Starting Jira Chatbot API with multi-user support")

    # Check if data directory exists, create if needed
    from pathlib import Path

    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    logger.info(f"Data directory: {data_dir}")

    # Initialize database
    from app.core.init_db import init_db

    init_db()
    logger.info("Database initialized successfully")

    # Check for encryption key
    encryption_key = os.environ.get("JIRA_TOKEN_ENCRYPTION_KEY", "")
    if not encryption_key:
        logger.warning(
            "No encryption key found in environment. A new key will be generated."
        )
    else:
        logger.info("Encryption key found in environment")

    # Check multi-user flag
    multi_user_enabled = (
        os.environ.get("JIRA_ENABLE_MULTI_USER", "true").lower() == "true"
    )
    logger.info(f"Multi-user mode: {'enabled' if multi_user_enabled else 'disabled'}")

    # Print URL info
    host = os.environ.get("HOST", "localhost")
    port = os.environ.get("PORT", "8000")
    logger.info(f"API available at: http://{host}:{port}/api")
    logger.info(f"Documentation at: http://{host}:{port}/docs")


# Health check endpoint
@app.get("/api/health")
async def health_check(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Health check endpoint for the extension"""
    is_authenticated = False
    token_info: Dict[str, Any] = {"present": False}
    debug_info: Dict[str, Any] = {}
    multi_user_enabled = (
        os.environ.get("JIRA_ENABLE_MULTI_USER", "true").lower() == "true"
    )
    server_version = "0.2.0"  # Version with multi-user support

    # Add database info
    database_info = {
        "url": os.environ.get("DATABASE_URL", "default sqlite"),
        "type": (
            "sqlite"
            if os.environ.get("DATABASE_URL", "").startswith("sqlite")
            else "custom"
        ),
    }

    # Get encryption info
    encryption_info = {
        "enabled": bool(os.environ.get("JIRA_TOKEN_ENCRYPTION_KEY", "")),
        "type": "Fernet symmetric encryption",
    }

    try:
        # Check for multi-user token if user_id is provided
        if user_id:
            from app.services.multi_user_jira_service import \
                MultiUserJiraService

            multi_service = MultiUserJiraService(db)
            jira_service = multi_service.get_jira_service(user_id)
            if jira_service:
                token = jira_service.get_oauth2_token()
                is_authenticated = token is not None
                token_info = {
                    "present": token is not None,
                    "type": "oauth2" if token else None,
                    "multi_user": True,
                    "expires_in": (
                        int(token.get("expires_at", 0) - datetime.now().timestamp())
                        if token
                        else None
                    ),
                }
                debug_info["user_id"] = user_id
                debug_info["user_type"] = (
                    "authenticated" if is_authenticated else "unauthenticated"
                )
                debug_info["multi_user"] = True
        else:
            # Legacy single-user check            from app.services.jira_service import jira_service
            if jira_service and hasattr(jira_service, "get_oauth2_token"):
                token = jira_service.get_oauth2_token()
                is_authenticated = token is not None
                token_info = {
                    "present": token is not None,
                    "type": "oauth2" if token else None,
                    "multi_user": False,
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

    # Get user count if multi-user is enabled
    user_count = 0
    if multi_user_enabled:
        try:
            from app.services.user_service import UserService

            user_service = UserService(db)
            users = user_service.list_users()
            user_count = len(users)
        except Exception as e:
            debug_info["user_count_error"] = str(e)

    # Return comprehensive health information
    return {
        "status": "ok",
        "version": server_version,
        "authenticated": is_authenticated,
        "token_info": token_info,
        "multi_user": {
            "enabled": multi_user_enabled,
            "user_count": user_count,
            "encryption": encryption_info,
        },
        "database": database_info,
        "debug": debug_info,
        "timestamp": datetime.now().isoformat(),
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Jira Chatbot API",
        "version": "0.2.0",
        "features": [
            "Multi-user authentication",
            "Token encryption",
            "Database storage",
        ],
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": "/api/health",
        "token_dashboard_url": "/dashboard/token",
        "multi_user_docs": "/docs#/oauth-multiuser",
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
        return {
            "error": "Dashboard file not found",
            "path": str(dashboard_file),
            "static_dir_exists": static_dir.exists(),
        }

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
