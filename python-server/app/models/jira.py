from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class JiraIssueBase(BaseModel):
    """Base model for Jira issue data"""

    summary: str
    description: Optional[str] = ""
    issue_type: str = "Task"
    project_key: str


class JiraIssueCreate(JiraIssueBase):
    """Model for creating a Jira issue"""

    assignee: Optional[str] = None
    components: Optional[List[str]] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    labels: Optional[List[str]] = None
    additional_fields: Optional[Dict[str, Any]] = None


class JiraIssueUpdate(BaseModel):
    """Model for updating a Jira issue"""

    summary: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[str] = None
    components: Optional[List[str]] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    labels: Optional[List[str]] = None
    additional_fields: Optional[Dict[str, Any]] = None


class JiraComment(BaseModel):
    """Model for a Jira comment"""

    body: str


class JiraTransition(BaseModel):
    """Model for transitioning a Jira issue"""

    transition_id: str
    comment: Optional[str] = None


class JiraSearchQuery(BaseModel):
    """Model for a Jira search query"""

    jql: str
    max_results: int = 20
    fields: Optional[List[str]] = None


class OAuthToken(BaseModel):
    """Model for OAuth 2.0 token"""

    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
