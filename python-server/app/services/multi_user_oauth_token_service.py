"""
Multi-User OAuth Token Background Refresh Service

This module implements a background service that continuously monitors OAuth tokens
for multiple users stored in the database and refreshes them proactively before
they expire. This ensures tokens are always fresh for all users, including those
with extended "Remember Me" sessions.

Features:
- Multi-user token monitoring with database integration
- Support for extended session durations
- Periodic checking of token expiration across all users
- Proactive refresh before expiration
- Event notification system
- Comprehensive logging
- Retry mechanisms for failed refreshes
- Integration with existing OAuth endpoints

For implementation in Phase 1, Day 8-9 (May 21-22, 2025)
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import requests
from app.core.database import get_db
from app.models.token import OAuthToken
from app.services.db_token_service import DBTokenService
from requests_oauthlib import OAuth2Session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MultiUserTokenRefreshEvent:
    """Class representing a multi-user token refresh event"""

    def __init__(
        self,
        event_type: str,
        message: str,
        user_id: Optional[str] = None,
        provider: str = "jira",
        token_info: Optional[Dict[str, Any]] = None,
    ):
        self.event_type = event_type  # "refresh", "error", "warning", "info"
        self.message = message
        self.timestamp = datetime.now()
        self.user_id = user_id
        self.provider = provider
        self.token_info = token_info or {}  # Masked token info


class MultiUserOAuthTokenService:
    """Service to manage OAuth tokens for multiple users with background refresh"""

    # Class-level flag to track if refresh thread is running
    _refresh_thread_running = False
    # Singleton instance to prevent multiple services
    _instance = None
    _lock_singleton = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one token service instance"""
        with cls._lock_singleton:
            if cls._instance is None:
                cls._instance = super(MultiUserOAuthTokenService, cls).__new__(cls)
            return cls._instance

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        check_interval: int = 300,  # 5 minutes
        refresh_threshold: int = 600,  # 10 minutes before expiry
        max_retries: int = 3,
        retry_delay: int = 30,  # 30 seconds between retries
    ):
        """Initialize Multi-User OAuth token service with background refresh

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            token_url: URL for token refresh
            check_interval: How often to check token status (seconds)
            refresh_threshold: When to refresh token before expiration (seconds)
            max_retries: Maximum number of retry attempts for refresh
            retry_delay: Delay between retry attempts (seconds)
        """
        # Only initialize once due to singleton pattern
        if hasattr(self, "_initialized"):
            return

        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.check_interval = check_interval
        self.refresh_threshold = refresh_threshold
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Thread control
        self._stop_event = threading.Event()
        self._refresh_thread = None
        self._lock = threading.Lock()

        # Event handling
        self._event_handlers: List[Callable[[MultiUserTokenRefreshEvent], None]] = []
        self._event_history: List[MultiUserTokenRefreshEvent] = []  # Statistics

        # Statistics tracking
        self.stats: Dict[str, Any] = {
            "refreshes_attempted": 0,
            "refreshes_succeeded": 0,
            "refreshes_failed": 0,
            "last_refresh": None,
            "next_scheduled_check": None,
            "active_users": 0,
            "extended_sessions": 0,
        }

        # Mark as initialized
        self._initialized = True

    def start(self):
        """Start the background token refresh thread"""
        # Class-level check to prevent multiple instances
        if MultiUserOAuthTokenService._refresh_thread_running:
            logger.debug("Multi-user OAuth token refresh service already running")
            return

        if self._refresh_thread and self._refresh_thread.is_alive():
            logger.debug("Token refresh thread already running for this instance")
            return

        self._stop_event.clear()
        self._refresh_thread = threading.Thread(
            target=self._background_refresh_loop,
            daemon=True,
            name="MultiUserOAuthTokenRefreshThread",
        )
        self._refresh_thread.start()
        MultiUserOAuthTokenService._refresh_thread_running = True

        logger.info("Started multi-user OAuth token background refresh service")
        self._notify_event(
            "info", "Multi-user OAuth token background refresh service started"
        )

    def stop(self):
        """Stop the background token refresh thread"""
        MultiUserOAuthTokenService._refresh_thread_running = False

        if not self._refresh_thread or not self._refresh_thread.is_alive():
            logger.warning("Multi-user token refresh thread not running")
            return

        logger.info("Stopping multi-user OAuth token background refresh service...")
        self._stop_event.set()
        self._refresh_thread.join(timeout=10)

        if self._refresh_thread.is_alive():
            logger.warning("Multi-user token refresh thread did not stop cleanly")
        else:
            logger.info("Multi-user OAuth token background refresh service stopped")
            self._notify_event(
                "info", "Multi-user OAuth token background refresh service stopped"
            )

    def add_event_handler(self, handler: Callable[[MultiUserTokenRefreshEvent], None]):
        """Add an event handler for token refresh events"""
        self._event_handlers.append(handler)

    def _notify_event(
        self,
        event_type: str,
        message: str,
        user_id: Optional[str] = None,
        provider: str = "jira",
        token_info: Optional[Dict[str, Any]] = None,
    ):
        """Notify all event handlers of a token event"""
        # Create event and store in history
        event = MultiUserTokenRefreshEvent(
            event_type, message, user_id, provider, token_info
        )
        with self._lock:
            self._event_history.append(event)
            # Keep only the last 500 events (more for multi-user)
            if len(self._event_history) > 500:
                self._event_history = self._event_history[-500:]

        # Notify handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {str(e)}")

    def _background_refresh_loop(self):
        """Main background loop to check and refresh tokens"""
        logger.info("Multi-user token refresh background loop started")

        while not self._stop_event.is_set():
            try:
                # Update next check time
                self.stats["next_scheduled_check"] = datetime.now() + timedelta(
                    seconds=self.check_interval
                )

                # Check and refresh tokens
                self._check_and_refresh_all_tokens()

                # Sleep for the specified interval
                if not self._stop_event.wait(self.check_interval):
                    continue  # Continue if not stopped

            except Exception as e:
                logger.error(f"Error in background refresh loop: {str(e)}")
                self._notify_event("error", f"Background refresh loop error: {str(e)}")
                # Sleep a bit before retrying
                self._stop_event.wait(min(self.check_interval, 60))

        logger.info("Multi-user token refresh background loop stopped")

    def _check_and_refresh_all_tokens(self):
        """Check all user tokens and refresh those that need it"""
        try:
            # Get database session
            db = next(get_db())
            db_token_service = DBTokenService(db)

            # Get tokens that need refreshing
            tokens_needing_refresh = db_token_service.get_tokens_needing_refresh(
                self.refresh_threshold
            )

            # Update statistics
            all_active_tokens = db_token_service.list_active_tokens()
            self.stats["active_users"] = len(all_active_tokens)
            self.stats["extended_sessions"] = len(
                [t for t in all_active_tokens if t.is_extended_session]
            )

            if not tokens_needing_refresh:
                logger.debug(
                    f"No tokens need refreshing. Active users: {self.stats['active_users']}, Extended sessions: {self.stats['extended_sessions']}"
                )
                return

            logger.info(f"Found {len(tokens_needing_refresh)} tokens needing refresh")

            # Refresh each token
            for token in tokens_needing_refresh:
                if self._stop_event.is_set():
                    break

                try:
                    self._refresh_user_token(token, db_token_service)
                except Exception as e:
                    logger.error(
                        f"Error refreshing token for user {token.user_id}: {str(e)}"
                    )
                    self._notify_event(
                        "error",
                        f"Failed to refresh token: {str(e)}",
                        token.user_id,
                        token.provider,
                    )

        except Exception as e:
            logger.error(f"Error in check and refresh all tokens: {str(e)}")
            self._notify_event("error", f"Error checking tokens: {str(e)}")
        finally:
            db.close()

    def _refresh_user_token(self, token: OAuthToken, db_token_service: DBTokenService):
        """Refresh a single user's token"""
        user_id = token.user_id
        provider = token.provider

        logger.info(
            f"Attempting to refresh token for user {user_id} (extended: {token.is_extended_session})"
        )

        for attempt in range(self.max_retries):
            try:
                self.stats["refreshes_attempted"] += 1

                # Prepare refresh request
                refresh_data = {
                    "grant_type": "refresh_token",
                    "refresh_token": token.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }

                # Make refresh request
                response = requests.post(
                    self.token_url,
                    data=refresh_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30,
                )

                if response.status_code == 200:
                    # Successful refresh
                    new_token_data = response.json()

                    # Add expires_at if not present
                    if (
                        "expires_at" not in new_token_data
                        and "expires_in" in new_token_data
                    ):
                        expires_in = new_token_data["expires_in"]
                        new_token_data["expires_at"] = (
                            datetime.now().timestamp() + expires_in
                        )

                    # Update token in database (preserving extended session settings)
                    updated_token = db_token_service.update_token_from_refresh(
                        user_id, new_token_data, provider
                    )

                    if updated_token:
                        self.stats["refreshes_succeeded"] += 1
                        self.stats["last_refresh"] = datetime.now()

                        logger.info(f"Successfully refreshed token for user {user_id}")
                        self._notify_event(
                            "refresh",
                            f"Token refreshed successfully",
                            user_id,
                            provider,
                            {
                                "expires_at": updated_token.effective_expires_at,
                                "is_extended": updated_token.is_extended_session,
                                "seconds_to_expiry": updated_token.seconds_to_expiry,
                            },
                        )
                        return
                    else:
                        raise Exception("Failed to update token in database")

                else:
                    # Failed refresh
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(
                        f"Token refresh failed for user {user_id}, attempt {attempt + 1}: {error_msg}"
                    )

                    if response.status_code in [400, 401]:
                        # Refresh token is invalid/expired, mark token inactive
                        db_token_service.mark_token_inactive(user_id, provider)
                        logger.warning(
                            f"Marked token as inactive for user {user_id} due to invalid refresh token"
                        )
                        self._notify_event(
                            "warning",
                            f"Token marked inactive due to invalid refresh token",
                            user_id,
                            provider,
                        )
                        return

                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise Exception(error_msg)

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Network error refreshing token for user {user_id}, attempt {attempt + 1}: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
            except Exception as e:
                logger.error(
                    f"Unexpected error refreshing token for user {user_id}, attempt {attempt + 1}: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise

        # If we get here, all retries failed
        self.stats["refreshes_failed"] += 1
        raise Exception(f"Failed to refresh token after {self.max_retries} attempts")

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return self.stats.copy()

    def get_event_history(self, limit: int = 50) -> List[MultiUserTokenRefreshEvent]:
        """Get recent event history"""
        with self._lock:
            return self._event_history[-limit:] if self._event_history else []

    def force_refresh_user_token(self, user_id: str, provider: str = "jira") -> bool:
        """Force refresh of a specific user's token"""
        try:
            db = next(get_db())
            db_token_service = DBTokenService(db)

            token = db_token_service.get_token(user_id, provider)
            if not token:
                logger.warning(f"No token found for user {user_id}")
                return False

            if not token.refresh_token:
                logger.warning(f"No refresh token available for user {user_id}")
                return False

            self._refresh_user_token(token, db_token_service)
            return True

        except Exception as e:
            logger.error(f"Error force refreshing token for user {user_id}: {str(e)}")
            return False
        finally:
            db.close()

    def cleanup_expired_tokens(self):
        """Clean up expired tokens that can't be refreshed"""
        try:
            db = next(get_db())
            db_token_service = DBTokenService(db)

            expired_tokens = db_token_service.get_expired_tokens()

            for token in expired_tokens:
                if not token.refresh_token:
                    # No refresh token, mark as inactive
                    db_token_service.mark_token_inactive(token.user_id, token.provider)
                    logger.info(
                        f"Cleaned up expired token for user {token.user_id} (no refresh token)"
                    )
                    self._notify_event(
                        "info",
                        "Expired token cleaned up (no refresh token)",
                        token.user_id,
                        token.provider,
                    )

        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
        finally:
            db.close()
