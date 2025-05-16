from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class JiraIssue(BaseModel):
    """Schema for a Jira issue"""
    key: str
    summary: str
    description: Optional[str] = None
    issue_type: str
    assignee: Optional[str] = None
    assignee_display_name: Optional[str] = None
    status: str
    priority: Optional[str] = None
    due_date: Optional[str] = None
    created_date: str
    updated_date: str
    project_key: str
    project_name: str
    labels: List[str] = []
    url: str
    attachments: List[Dict[str, Any]] = []
    comments: List[Dict[str, Any]] = []


class User(BaseModel):
    """Schema for user information"""
    username: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
