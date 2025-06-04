"""
Jira User Sync Service for synchronizing user data from Jira Cloud to local database.

This service retrieves all users from Jira Cloud and stores/updates their account information
in the local database for fast lookup during assignee operations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from app.core.config import settings
from app.models.user import User
from app.services.jira_service import JiraService
from app.services.user_service import UserService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class JiraUserSyncService:
    """Service for syncing Jira users to the local database"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.user_service = UserService(db)

    def sync_users_from_jira(self) -> Dict[str, Any]:
        """
        Sync all users from Jira Cloud to the local database.

        Returns:
            Dict with sync results (users_processed, users_updated, errors)
        """
        logger.info("Starting Jira user synchronization...")

        try:
            # Create JiraService with API token (not user-specific OAuth)
            jira_service = JiraService()

            if not jira_service.is_connected():
                logger.error("Cannot connect to Jira API for user sync")
                return {
                    "success": False,
                    "error": "Cannot connect to Jira API",
                    "users_processed": 0,
                    "users_updated": 0,
                }  # Get all users from Jira
            logger.info("Retrieving users from Jira Cloud...")
            jira_users = jira_service.get_all_users()  # type: ignore

            if not jira_users:
                logger.warning("No users retrieved from Jira Cloud")
                return {
                    "success": True,
                    "message": "No users found in Jira",
                    "users_processed": 0,
                    "users_updated": 0,
                }

            users_processed = 0
            users_updated = 0
            errors = []

            logger.info(f"Processing {len(jira_users)} users from Jira...")

            for jira_user in jira_users:
                try:
                    account_id = jira_user.get("accountId")
                    display_name = jira_user.get("displayName", "")
                    email_address = jira_user.get("emailAddress", "")
                    active = jira_user.get("active", True)

                    if not account_id:
                        logger.warning(f"Skipping user without accountId: {jira_user}")
                        continue
                    # Find existing user by jira_account_id
                    existing_user = (
                        self.db.query(User)
                        .filter(User.jira_account_id == account_id)
                        .first()
                    )

                    if existing_user:
                        # Update existing user
                        updated = False
                        if existing_user.display_name != display_name:
                            existing_user.display_name = display_name
                            updated = True
                        if existing_user.email != email_address:
                            existing_user.email = email_address
                            updated = True
                        if existing_user.is_active != active:
                            existing_user.is_active = active
                            updated = True

                        if updated:
                            existing_user.updated_at = datetime.utcnow()  # type: ignore
                            users_updated += 1
                            logger.debug(f"Updated user: {display_name} ({account_id})")
                    else:
                        # Create new user
                        new_user = User(
                            jira_account_id=account_id,
                            display_name=display_name,
                            email=email_address,
                            is_active=active,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                        self.db.add(new_user)
                        users_updated += 1
                        logger.debug(f"Created new user: {display_name} ({account_id})")

                    users_processed += 1

                except Exception as user_error:
                    error_msg = f"Error processing user {jira_user}: {str(user_error)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            # Commit all changes
            self.db.commit()

            logger.info(
                f"User sync completed: {users_processed} processed, {users_updated} updated"
            )

            return {
                "success": True,
                "users_processed": users_processed,
                "users_updated": users_updated,
                "errors": errors,
                "message": f"Successfully synced {users_updated} users from Jira",
            }

        except Exception as e:
            logger.error(f"Error during Jira user synchronization: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "users_processed": 0,
                "users_updated": 0,
            }

    def sync_single_user_by_display_name(
        self, display_name: str, jira_service: JiraService
    ) -> Dict[str, Any]:
        """
        Sync a single user by display name from Jira to local database.
        This is used when we encounter a user that's not in our database.

        Args:
            display_name: The display name to search for
            jira_service: JiraService instance to use for the lookup

        Returns:
            Dict with sync result and user info
        """
        try:
            logger.info(
                f"Syncing single user by display name: {display_name}"
            )  # Find user in Jira
            jira_user = jira_service.find_user_by_display_name(display_name)  # type: ignore

            if not jira_user:
                return {
                    "success": False,
                    "error": f"User '{display_name}' not found in Jira",
                }

            account_id = jira_user.get("accountId")
            email_address = jira_user.get("emailAddress", "")
            active = jira_user.get("active", True)

            if not account_id:
                return {
                    "success": False,
                    "error": f"User '{display_name}' found but has no accountId",
                }

            # Check if user already exists in database
            existing_user = (
                self.db.query(User).filter(User.jira_account_id == account_id).first()
            )

            if existing_user:
                logger.info(f"User {display_name} already exists in database")
                return {
                    "success": True,
                    "user": existing_user,
                    "account_id": account_id,
                    "message": "User already exists in database",
                }
            # Create new user
            new_user = User(
                jira_account_id=account_id,
                display_name=display_name,
                email=email_address,
                is_active=active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(new_user)
            self.db.commit()

            logger.info(f"Successfully synced user: {display_name} ({account_id})")

            return {
                "success": True,
                "user": new_user,
                "account_id": account_id,
                "message": f"Successfully synced user '{display_name}' from Jira",
            }

        except Exception as e:
            logger.error(f"Error syncing single user '{display_name}': {str(e)}")
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def get_sync_stats(self) -> Dict[str, Any]:
        """
        Get statistics about synced users in the database.

        Returns:
            Dict with user count statistics
        """
        try:
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active.is_(True)).count()
            jira_users = (
                self.db.query(User).filter(User.jira_account_id.isnot(None)).count()
            )

            return {
                "total_users": total_users,
                "active_users": active_users,
                "jira_users": jira_users,
                "inactive_users": total_users - active_users,
            }

        except Exception as e:
            logger.error(f"Error getting sync stats: {str(e)}")
            return {"error": str(e)}


class BackgroundUserSyncService:
    """Background service for periodic user synchronization"""

    def __init__(self, db_session_factory):
        """Initialize with database session factory"""
        self.db_session_factory = db_session_factory
        self.sync_interval = 24 * 60 * 60  # 24 hours in seconds
        self.running = False

    async def start_background_sync(self):
        """Start the background synchronization process"""
        logger.info("Starting background user sync service...")
        self.running = True

        while self.running:
            try:
                # Create a new database session for this sync
                db = self.db_session_factory()
                try:
                    sync_service = JiraUserSyncService(db)
                    result = sync_service.sync_users_from_jira()

                    if result["success"]:
                        logger.info(
                            f"Background sync completed: {result.get('message', 'Unknown result')}"
                        )
                    else:
                        logger.error(
                            f"Background sync failed: {result.get('error', 'Unknown error')}"
                        )

                finally:
                    db.close()

                # Wait for next sync interval
                await asyncio.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Error in background user sync: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    def stop_background_sync(self):
        """Stop the background synchronization process"""
        logger.info("Stopping background user sync service...")
        self.running = False
