#!/usr/bin/env python3
"""
Multi-user Authentication Test Script

This script helps test the multi-user authentication system by creating test users
and performing basic operations.

Usage:
    python -m app.scripts.test_multi_user
"""

import logging
import sys
import uuid
from datetime import datetime

from app.core.database import SessionLocal
from app.models.user import User
from app.services.db_token_service import DBTokenService
from app.services.user_service import UserService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("multi_user_test.log")],
)
logger = logging.getLogger(__name__)
logger.info("Test Multi-User script started")


def create_test_user():
    """Create a test user and return the user ID"""
    print("Creating test user...")
    db = SessionLocal()
    try:
        # Create user service
        user_service = UserService(db)

        # Generate unique email
        unique_id = uuid.uuid4().hex[:8]
        email = f"test.user.{unique_id}@example.com"

        # Create test user with user_data dictionary
        user_data = {
            "email": email,
            "display_name": f"Test User {unique_id}",
            "is_active": True,
        }

        print(f"Creating user with email: {email}")
        # Use get_or_create_user since it's available in UserService
        created_user = user_service.get_or_create_user(user_data)
        print(f"Created test user with ID: {created_user.id}")
        print(f"Test user email: {created_user.email}")
        logger.info(f"Created test user with ID: {created_user.id}")
        logger.info(f"Test user email: {created_user.email}")

        return created_user.id
    finally:
        db.close()


def simulate_oauth_flow(user_id):
    """Simulate OAuth flow for a user by creating a mock token"""
    db = SessionLocal()
    try:
        # Create token service
        token_service = DBTokenService(db)

        # Mock token data
        mock_token = {
            "access_token": f"mock_access_token_{uuid.uuid4().hex}",
            "refresh_token": f"mock_refresh_token_{uuid.uuid4().hex}",
            "token_type": "Bearer",
            "expires_at": datetime.now().timestamp() + 3600,  # 1 hour expiry
            "scope": "read:jira-work write:jira-work",
            "additional_data": {
                "is_test": True,
                "created_at": datetime.now().isoformat(),
            },
        }

        # Store token
        token = token_service.store_token(user_id, mock_token)
        logger.info(f"Created mock token for user {user_id}")

        # Test token retrieval
        retrieved_token = token_service.get_token(user_id)
        if retrieved_token:
            logger.info(f"Successfully retrieved token for user {user_id}")
            logger.info(
                f"Token expires at: {datetime.fromtimestamp(retrieved_token.expires_at)}"
            )
            return True
        else:
            logger.error(f"Failed to retrieve token for user {user_id}")
            return False
    finally:
        db.close()


def run_tests():
    """Run a series of tests for multi-user authentication"""
    logger.info("Starting multi-user authentication tests...")

    # Create test user
    user_id = create_test_user()

    # Simulate OAuth flow
    if simulate_oauth_flow(user_id):
        logger.info("OAuth flow simulation successful")
    else:
        logger.error("OAuth flow simulation failed")
        return False

    # Provide instructions for testing with the API
    logger.info("\nTest Instructions:")
    logger.info(f"1. Use this user ID for API testing: {user_id}")
    logger.info(f"2. Try the health endpoint: GET /api/health?user_id={user_id}")
    logger.info(
        f"3. Check token status: GET /api/auth/oauth/v2/status?user_id={user_id}"
    )
    logger.info(
        f"4. Try listing Jira projects: GET /api/jira/v2/projects?user_id={user_id}"
    )

    return True


if __name__ == "__main__":
    success = run_tests()
    if success:
        logger.info("All tests completed successfully")
        sys.exit(0)
    else:
        logger.error("Tests failed")
        sys.exit(1)
