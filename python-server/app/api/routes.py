from fastapi import APIRouter

from app.api.endpoints import chat, jira, health

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(jira.router, prefix="/jira", tags=["jira"])
