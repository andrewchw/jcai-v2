#!/usr/bin/env python3
"""
OAuth Token Background Refresh Service

This module implements a background thread that continuously monitors OAuth tokens
and refreshes them proactively before they expire. This eliminates the need to
refresh tokens only when API calls are made, ensuring tokens are always fresh.

Features:
- Dedicated background thread for token monitoring
- Periodic checking of token expiration
- Proactive refresh before expiration
- Event notification system
- Comprehensive logging
- Retry mechanisms for failed refreshes
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("oauth_token_service.log")],
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class TokenRefreshEvent:
    """Class representing a token refresh event"""

    def __init__(
        self, event_type: str, message: str, token_info: Optional[Dict[str, Any]] = None
    ):
        self.event_type = event_type  # "refresh", "error", "warning", "info"
        self.message = message
        self.timestamp = datetime.now()
        self.token_info = token_info or {}  # Masked token info


class OAuthTokenService:
    # Class-level flag to track if any refresh thread is running
    _refresh_thread_running = False

    """Service to manage OAuth tokens with background refresh"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        token_file: str,
        check_interval: int = 300,  # 5 minutes
        refresh_threshold: int = 600,  # 10 minutes
        max_retries: int = 3,
    ):
        """Initialize OAuth token service with background refresh

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            token_url: URL for token refresh
            token_file: Path to token storage file
            check_interval: How often to check token status (seconds)
            refresh_threshold: When to refresh token before expiration (seconds)
            max_retries: Maximum number of retry attempts for refresh
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.token_file = token_file
        self.check_interval = check_interval
        self.refresh_threshold = refresh_threshold
        self.max_retries = max_retries

        # Thread control
        self._stop_event = threading.Event()
        self._refresh_thread = None
        self._lock = threading.Lock()

        # Event handling
        self._event_handlers: List[Callable[[TokenRefreshEvent], None]] = []
        self._event_history: List[TokenRefreshEvent] = []
        # Statistics
        self.stats: Dict[str, Any] = {
            "refreshes_attempted": 0,
            "refreshes_succeeded": 0,
            "refreshes_failed": 0,
            "last_refresh": None,
            "next_scheduled_check": None,
        }

    def start(self):
        """Start the background token refresh thread"""
        # Class-level check to prevent multiple instances across different objects
        if OAuthTokenService._refresh_thread_running:
            logger.warning("Another OAuth token refresh service is already running")
            return

        if self._refresh_thread and self._refresh_thread.is_alive():
            logger.warning("Token refresh thread already running")
            return

        self._stop_event.clear()
        self._refresh_thread = threading.Thread(
            target=self._background_refresh_loop,
            daemon=True,
            name="OAuthTokenRefreshThread",
        )
        self._refresh_thread.start()
        # Set the running flag
        OAuthTokenService._refresh_thread_running = True

        logger.info("Started OAuth token background refresh service")
        self._notify_event("info", "OAuth token background refresh service started")

    def stop(self):
        """Stop the background token refresh thread"""
        # Reset the class-level running flag when stopping
        OAuthTokenService._refresh_thread_running = False

        if not self._refresh_thread or not self._refresh_thread.is_alive():
            logger.warning("Token refresh thread not running")
            return

        logger.info("Stopping OAuth token background refresh service...")
        self._stop_event.set()
        self._refresh_thread.join(timeout=10)

        if self._refresh_thread.is_alive():
            logger.warning("Token refresh thread did not stop cleanly")
        else:
            logger.info("OAuth token background refresh service stopped")
            self._notify_event("info", "OAuth token background refresh service stopped")

    def add_event_handler(self, handler: Callable[[TokenRefreshEvent], None]):
        """Add an event handler for token refresh events

        Args:
            handler: Callback function taking a TokenRefreshEvent parameter
        """
        self._event_handlers.append(handler)

    def _notify_event(
        self, event_type: str, message: str, token_info: Optional[Dict[str, Any]] = None
    ):
        """Notify all event handlers of a token event"""
        # Create event and store in history
        event = TokenRefreshEvent(event_type, message, token_info)
        with self._lock:
            self._event_history.append(event)
            # Keep only the last 100 events
            if len(self._event_history) > 100:
                self._event_history = self._event_history[-100:]

        # Notify handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {str(e)}")

    def load_token(self) -> Optional[Dict[str, Any]]:
        """Load OAuth token from file"""
        try:
            if os.path.exists(self.token_file):
                with self._lock:
                    with open(self.token_file, "r") as f:
                        token = json.load(f)
                logger.info(f"Token loaded from {self.token_file}")
                return token
        except Exception as e:
            logger.error(f"Could not load token: {str(e)}")
            self._notify_event("error", f"Failed to load token: {str(e)}")

        return None

    def save_token(self, token: Dict[str, Any]) -> bool:
        """Save OAuth token to file"""
        try:
            with self._lock:
                with open(self.token_file, "w") as f:
                    json.dump(token, f)
            logger.info(f"Token saved to {self.token_file}")
            return True
        except Exception as e:
            logger.error(f"Could not save token: {str(e)}")
            self._notify_event("error", f"Failed to save token: {str(e)}")
            return False

    def _mask_token_for_logs(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Create a masked copy of token for logging/events"""
        if not token:
            return {}

        masked = token.copy()

        # Mask sensitive fields
        for field in ["access_token", "refresh_token"]:
            if field in masked:
                value = masked[field]
                if len(value) > 15:
                    masked[field] = value[:5] + "..." + value[-5:]
                else:
                    masked[field] = value[:3] + "..."

        return masked

    def refresh_token(
        self, token: Dict[str, Any], force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Refresh the OAuth token if needed or forced

        Args:
            token: The current token
            force: Force refresh even if not expired

        Returns:
            The new token if refreshed, original token if not, or None on error
        """
        if not token or "refresh_token" not in token:
            logger.error("Cannot refresh token: No refresh token available")
            self._notify_event(
                "error", "Cannot refresh token: No refresh token available"
            )
            return None

        needs_refresh = force
        time_remaining = None

        # Check if token is expired or about to expire
        if "expires_at" in token and not force:
            expires_at = token["expires_at"]
            current_time = datetime.now().timestamp()
            time_remaining = expires_at - current_time

            if time_remaining <= self.refresh_threshold:
                needs_refresh = True
                if time_remaining <= 0:
                    logger.info(
                        f"Token expired {timedelta(seconds=abs(time_remaining))} ago"
                    )
                else:
                    logger.info(
                        f"Token expires in {timedelta(seconds=time_remaining)}, within threshold"
                    )

        # Return original if no refresh needed
        if not needs_refresh:
            return token

        # Try to refresh the token
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                self.stats["refreshes_attempted"] += 1  # Log refresh attempt
                if retry_count == 0:
                    if force:
                        logger.info("Force refreshing token")
                        self._notify_event("info", "Force refreshing token")
                    else:
                        if time_remaining and time_remaining <= 0:
                            logger.info("Token expired, refreshing")
                            self._notify_event("info", "Token expired, refreshing")
                        else:
                            logger.info("Token expires soon, refreshing")
                            self._notify_event("info", "Token expires soon, refreshing")
                else:
                    logger.info(
                        f"Retrying token refresh (attempt {retry_count}/{self.max_retries})"
                    )

                # Create OAuth session and refresh
                oauth = OAuth2Session(self.client_id, token=token)
                new_token = oauth.refresh_token(
                    self.token_url,
                    refresh_token=token["refresh_token"],
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

                # Update expiration info
                if "expires_at" in new_token:
                    new_expires_at = new_token["expires_at"]
                    new_expiry = datetime.fromtimestamp(new_expires_at)
                    logger.info(
                        f"Token refreshed successfully! New expiration: {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                # Save the new token
                self.save_token(new_token)

                # Update stats
                self.stats["refreshes_succeeded"] += 1
                self.stats["last_refresh"] = datetime.now()

                # Notify success
                self._notify_event(
                    "refresh",
                    "Token refreshed successfully",
                    self._mask_token_for_logs(new_token),
                )

                return new_token

            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error refreshing token (attempt {retry_count}/{self.max_retries}): {str(e)}"
                )

                if retry_count <= self.max_retries:
                    # Exponential backoff: 2^retry_count seconds (2, 4, 8)
                    wait_time = 2**retry_count
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    self.stats["refreshes_failed"] += 1
                    self._notify_event(
                        "error",
                        f"Token refresh failed after {retry_count} attempts: {str(e)}",
                    )

        # All retries failed
        return None

    def invalidate_token(self) -> bool:
        """Invalidate the current OAuth token

        This method will delete the stored token file and reset any related state.
        Use this when logging out a user or when a token is known to be invalid.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(self.token_file):
                with self._lock:
                    # Remove the token file
                    os.remove(self.token_file)

                logger.info(f"Token invalidated and removed from {self.token_file}")
                self._notify_event("info", "Token invalidated successfully")

                # Reset relevant stats
                self.stats["last_refresh"] = None

                return True
            else:
                logger.info(
                    f"No token file found at {self.token_file}, nothing to invalidate"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to invalidate token: {str(e)}")
            self._notify_event("error", f"Failed to invalidate token: {str(e)}")
            return False

    def _background_refresh_loop(self):
        """Background thread function to check and refresh token periodically"""
        try:
            logger.info("Token refresh background thread started")

            while not self._stop_event.is_set():
                try:
                    # Load current token
                    token = self.load_token()

                    if not token:
                        logger.warning("No token available for background refresh")
                        self._notify_event(
                            "warning", "No token available for background refresh"
                        )
                    else:
                        # Check if refresh is needed
                        if "expires_at" in token:
                            expires_at = token["expires_at"]
                            current_time = datetime.now().timestamp()
                            time_remaining = expires_at - current_time

                            if time_remaining <= self.refresh_threshold:
                                # Token needs refresh
                                new_token = self.refresh_token(token)
                                if new_token:
                                    token = new_token
                            else:
                                # Token still valid
                                next_check = self.check_interval
                                time_to_refresh = (
                                    time_remaining - self.refresh_threshold
                                )

                                # If next check would miss the refresh window, adjust it
                                if time_to_refresh < self.check_interval:
                                    next_check = max(
                                        60, int(time_to_refresh)
                                    )  # Min 1 minute
                                    logger.info(
                                        f"Adjusting next check to {next_check} seconds to catch refresh window"
                                    )

                                logger.info(
                                    f"Token valid for {timedelta(seconds=time_remaining)}, next check in {next_check} seconds"
                                )

                                # Calculate and store next check time
                                self.stats[
                                    "next_scheduled_check"
                                ] = datetime.now() + timedelta(seconds=next_check)

                                # Sleep until next check, but can be interrupted by stop event
                                self._stop_event.wait(next_check)
                                continue
                        else:
                            logger.warning("Token has no expiration information")
                            self._notify_event(
                                "warning", "Token has no expiration information"
                            )

                    # Standard check interval
                    self.stats["next_scheduled_check"] = datetime.now() + timedelta(
                        seconds=self.check_interval
                    )
                    self._stop_event.wait(self.check_interval)

                except Exception as e:
                    logger.error(f"Error in token refresh background thread: {str(e)}")
                    self._notify_event("error", f"Background refresh error: {str(e)}")
                    # Sleep for a bit before trying again, but can be interrupted
                    self._stop_event.wait(60)  # 1 minute

            logger.info("Token refresh background thread stopped")

        finally:
            # Reset the class-level running flag when this method exits
            OAuthTokenService._refresh_thread_running = False


# Example of how to use this class
if (
    __name__ == "__main__"
):  # This is just for demonstration - would be implemented in main application
    TOKEN_FILE = os.getenv("TOKEN_FILE", "oauth_token.json")
    CLIENT_ID = os.getenv("JIRA_OAUTH_CLIENT_ID")
    CLIENT_SECRET = os.getenv("JIRA_OAUTH_CLIENT_SECRET")
    TOKEN_URL = "https://auth.atlassian.com/oauth/token"

    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: JIRA_OAUTH_CLIENT_ID and JIRA_OAUTH_CLIENT_SECRET must be set")
        exit(1)

    # Example event handler
    def log_event(event: TokenRefreshEvent):
        print(f"{event.timestamp}: [{event.event_type}] {event.message}")

    # Create service and add event handler
    token_service = OAuthTokenService(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_url=TOKEN_URL,
        token_file=TOKEN_FILE,
        check_interval=60,  # Check every minute for demo
        refresh_threshold=300,  # Refresh 5 minutes before expiry for demo
    )

    token_service.add_event_handler(log_event)

    # Start background service
    print("Starting OAuth token background refresh service...")
    token_service.start()

    try:  # Keep main thread alive for demonstration
        while True:
            print("\nService status:")
            print(
                f"- Refreshes attempted: {token_service.stats['refreshes_attempted']}"
            )
            print(
                f"- Refreshes succeeded: {token_service.stats['refreshes_succeeded']}"
            )
            print(f"- Refreshes failed: {token_service.stats['refreshes_failed']}")

            if token_service.stats["last_refresh"]:
                last_refresh = token_service.stats["last_refresh"]
                if isinstance(last_refresh, datetime):
                    print(
                        f"- Last refresh: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                else:
                    print(f"- Last refresh: {last_refresh}")

            if token_service.stats["next_scheduled_check"]:
                next_check = token_service.stats["next_scheduled_check"]
                if isinstance(next_check, datetime):
                    now = datetime.now()
                    if next_check > now:
                        time_to_check = (next_check - now).total_seconds()
                        print(
                            f"- Next check: {time_to_check:.0f} seconds from now ({next_check.strftime('%Y-%m-%d %H:%M:%S')})"
                        )
                    else:
                        print("- Next check: imminent")
                else:
                    print(f"- Next check: {next_check}")

            # Show current token status
            token = token_service.load_token()
            if token and "expires_at" in token:
                expires_at = token["expires_at"]
                current_time = datetime.now().timestamp()
                time_remaining = expires_at - current_time

                if time_remaining <= 0:
                    print(
                        f"- Token status: EXPIRED ({abs(time_remaining):.0f} seconds ago)"
                    )
                else:
                    print(
                        f"- Token status: valid for {time_remaining:.0f} seconds more"
                    )

                    # Show if within refresh threshold
                    if time_remaining <= token_service.refresh_threshold:
                        print(
                            f"  (Within refresh threshold of {token_service.refresh_threshold} seconds)"
                        )

            time.sleep(10)
    except KeyboardInterrupt:
        print("\nStopping service...")
        token_service.stop()
        print("Service stopped")
