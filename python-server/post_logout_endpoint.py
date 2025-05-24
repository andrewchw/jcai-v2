"""
POST Logout Endpoint

This file contains the code for adding a POST endpoint for the logout functionality.
Add this code right after the existing GET logout endpoint in oauth_multi.py.
"""

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from app.database import get_db  # Adjusted import path

# Create a router
router = APIRouter()

@router.post("/logout")
async def logout_post(
    user_id: str,
    db: Session = Depends(get_db)
):
    # This simply calls the same implementation as the GET endpoint
    # Import the logout function or implement it here
    from app.routers.oauth_multi import logout  # Adjusted import path
    return await logout(user_id=user_id, db=db)

