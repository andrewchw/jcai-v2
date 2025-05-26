from app.api.endpoints import chat, debug, jira, jira_multi, oauth, oauth_multi
from app.api.user_profile import \
    user_profile_router  # Import the new user profile router
from fastapi import APIRouter

api_router = APIRouter()

# Include Chat endpoints (Dialogflow-inspired)
api_router.include_router(chat.router, tags=["chat"])

# Include Jira endpoints
api_router.include_router(jira.router, prefix="/jira", tags=["jira"])

# Include OAuth monitoring endpoints
api_router.include_router(oauth.router, prefix="/auth", tags=["oauth"])

# Include multi-user Jira endpoints - Note: jira_multi.router already has its own prefix "/jira/v2"
api_router.include_router(jira_multi.router, tags=["jira-multiuser"])

# Include multi-user OAuth endpoints
api_router.include_router(oauth_multi.router, prefix="/auth", tags=["oauth-multiuser"])

# Include user profile endpoints
api_router.include_router(
    user_profile_router
)  # Default prefix '/user' is in user_profile.py

# Include debug endpoints
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
