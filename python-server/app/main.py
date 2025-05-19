from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import pathlib

from app.api.routes import api_router
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="Jira Chatbot API",
    description="API for Microsoft Edge Chatbot Extension for Jira",
    version="0.1.0",
)

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
    
    if not dashboard_file.exists():
        return {"error": "Dashboard file not found"}
        
    return FileResponse(dashboard_file)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "api_version": "0.1.0"
    }
