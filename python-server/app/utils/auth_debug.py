"""
Auth debug utilities for Jira OAuth2 flow.
This module provides functions to help debug authentication issues.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("oauth_debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger("auth_debug")


def log_token_details(token_data, source="manual_check"):
    """Log details about the current token state"""
    if not token_data:
        logger.warning(f"[{source}] No token data available")
        return

    # Remove sensitive information for logging
    safe_token = {}
    for key, value in token_data.items():
        if key in ["access_token", "refresh_token"]:
            # Only log first and last 4 chars
            if value and len(value) > 8:
                safe_token[key] = f"{value[:4]}...{value[-4:]}"
            else:
                safe_token[key] = "[REDACTED]"
        else:
            safe_token[key] = value

    # Add expiration information
    if "expires_at" in token_data:
        expires_at = datetime.fromtimestamp(token_data["expires_at"])
        now = datetime.now()
        delta = expires_at - now
        minutes = delta.total_seconds() / 60
        safe_token["expires_in_minutes"] = round(minutes, 2)
        safe_token["is_expired"] = minutes <= 0

    logger.info(f"[{source}] Token details: {json.dumps(safe_token, indent=2)}")


def save_token_backup():
    """Create a backup of the current token file"""
    token_path = Path("oauth_token.json")
    if not token_path.exists():
        logger.warning("No token file found to backup")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("token_backups")
    backup_dir.mkdir(exist_ok=True)

    backup_path = backup_dir / f"oauth_token_{timestamp}.json"

    try:
        with open(token_path, "r") as src:
            token_data = json.load(src)

        with open(backup_path, "w") as dest:
            json.dump(token_data, dest, indent=4)

        logger.info(f"Created token backup at {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Failed to backup token: {str(e)}")
        return None


def check_auth_state():
    """Check and log the current authentication state"""
    logger.info("Checking authentication state")

    # Check token file
    token_path = Path("oauth_token.json")
    if token_path.exists():
        try:
            with open(token_path, "r") as f:
                token_data = json.load(f)
                log_token_details(token_data, "file_check")
                return True
        except Exception as e:
            logger.error(f"Error reading token file: {str(e)}")
    else:
        logger.warning("No token file found")

    return False


# Create a decorator to log function calls for debugging
def log_auth_function(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise

    return wrapper


if __name__ == "__main__":
    # When run directly, perform a check
    logger.info("=== Manual auth state check initiated ===")
    if check_auth_state():
        logger.info("Auth token found and loaded")
    else:
        logger.warning("Auth token check failed")
    logger.info("=== Auth state check completed ===")
