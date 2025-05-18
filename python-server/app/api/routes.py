from fastapi import APIRouter
from app.api.endpoints import jira

api_router = APIRouter()

# Include Jira endpoints
api_router.include_router(jira.router, prefix="/jira", tags=["jira"])
