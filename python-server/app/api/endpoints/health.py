from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def healthcheck():
    """
    Basic health check endpoint to verify the API is running.
    """
    return {
        "status": "healthy",
        "message": "Jira Chatbot AI Assistant API is operational"
    }
