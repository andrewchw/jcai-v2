"""
Configuration module for multi-user features.

This module contains constants and configuration values for multi-user authentication.
"""

import os
from typing import Any, Dict

# Feature flags
ENABLE_MULTI_USER = os.environ.get("JIRA_ENABLE_MULTI_USER", "true").lower() == "true"

# Database settings
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/tokens.db")

# Token encryption key
TOKEN_ENCRYPTION_KEY = os.environ.get("JIRA_TOKEN_ENCRYPTION_KEY", "")

# Default user settings
DEFAULT_USER_EMAIL = os.environ.get("JIRA_DEFAULT_USER_EMAIL", "default@example.com")
