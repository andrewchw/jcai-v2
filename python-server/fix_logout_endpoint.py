import os
import sys
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.multi_user_jira_service import MultiUserJiraService

# This script will update the OAuth V2 endpoint to accept POST requests for logout
# It creates a fixed version of the endpoint that can be added to oauth_multi.py

def update_logout_endpoint():
    """
    Creates code for an updated logout endpoint that accepts both GET and POST requests
    """
    return """
@router.post("/logout")
async def logout_post(
    user_id: str,
    db: Session = Depends(get_db)
):
    \"\"\"Logout and invalidate OAuth token for a user via POST request\"\"\"
    # This simply calls the same implementation as the GET endpoint
    return await logout(user_id=user_id, db=db)
"""

if __name__ == "__main__":
    print("Here is the code to add to oauth_multi.py:")
    print("-----------------------------------------")
    print(update_logout_endpoint())
    print("-----------------------------------------")
    print("Add this code right after the existing GET logout endpoint")
