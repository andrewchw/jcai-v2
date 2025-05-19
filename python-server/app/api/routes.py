from fastapi import APIRouter
from app.api.endpoints import jira, oauth

api_router = APIRouter()

# Include Jira endpoints
api_router.include_router(jira.router, prefix="/jira", tags=["jira"])

# Include OAuth monitoring endpoints
api_router.include_router(oauth.router, prefix="/auth", tags=["oauth"])
