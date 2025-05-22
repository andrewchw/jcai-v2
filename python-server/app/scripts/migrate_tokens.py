#!/usr/bin/env python3
"""
Token Migration Script

This script migrates tokens from the old file-based storage to the new database-backed storage system.
It creates a default user for each existing token and associates the token with that user.

Usage:
    python -m app.scripts.migrate_tokens
"""

import os
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required modules
from app.core.database import SessionLocal
from app.models.user import User
from app.models.token import OAuthToken
from app.services.oauth_token_service import OAuth2TokenService
from app.services.db_token_service import DBTokenService
from app.services.user_service import UserService

def migrate_tokens():
    """
    Migrate tokens from file-based storage to database
    """
    # Create a database session
    db = SessionLocal()
    
    try:
        # Initialize services
        old_service = OAuth2TokenService()
        db_token_service = DBTokenService(db)
        user_service = UserService(db)
        
        # Get existing token if any
        old_token = old_service.get_token()
        
        if not old_token:
            logger.warning("No existing token found. Nothing to migrate.")
            return
        
        logger.info("Found existing token. Starting migration...")
        
        # Create a default user for the existing token
        default_user = User(
            email=os.environ.get("DEFAULT_USER_EMAIL", "default@example.com"),
            display_name="Default User (Migrated)",
            is_active=True,
            last_login=datetime.now()
        )
        user = user_service.create_user(default_user)
        logger.info(f"Created default user with ID: {user.id}")
        
        # Migrate the token
        token_data = {
            "access_token": old_token.get("access_token"),
            "refresh_token": old_token.get("refresh_token"),
            "token_type": old_token.get("token_type", "Bearer"),
            "expires_at": old_token.get("expires_at") or (datetime.now().timestamp() + 3600),
            "scope": old_token.get("scope", ""),
            "additional_data": {
                "migrated_from": "file",
                "migration_date": datetime.now().isoformat()
            }
        }
        
        # Store token in database
        new_token = db_token_service.store_token(user.id, token_data)
        logger.info(f"Token migrated successfully for user {user.id}")
        
        # Backup old token file
        token_file = old_service.token_file
        if os.path.exists(token_file):
            backup_file = f"{token_file}.bak.{int(datetime.now().timestamp())}"
            os.rename(token_file, backup_file)
            logger.info(f"Backed up old token file to {backup_file}")
        
        return {
            "success": True,
            "user_id": user.id,
            "message": "Token migrated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error during token migration: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()

if __name__ == "__main__":
    # Run migration
    result = migrate_tokens()
    if result and result.get("success"):
        logger.info("Migration completed successfully")
        logger.info(f"User ID for migrated token: {result.get('user_id')}")
    else:
        logger.error("Migration failed")
        if result and result.get("error"):
            logger.error(f"Error: {result.get('error')}")
