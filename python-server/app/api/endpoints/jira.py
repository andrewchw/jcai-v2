"""Jira API endpoints."""

from typing import Any, Dict

from app.models.jira import (JiraComment, JiraIssueCreate, JiraIssueUpdate,
                             JiraSearchQuery, JiraTransition, OAuthToken)
from app.services.jira_service import jira_service
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check if the Jira API is connected and working"""
    is_connected = jira_service.is_connected()
    return {
        "status": "connected" if is_connected else "disconnected",
        "message": (
            "Jira API is connected" if is_connected else "Jira API is not connected"
        ),
    }


@router.post("/oauth/token")
async def set_oauth_token(token: OAuthToken):
    """Set OAuth 2.0 token for Jira API"""
    token_dict = token.dict()
    jira_service.set_oauth2_token(token_dict)

    # Test if the token works
    is_connected = jira_service.is_connected()
    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OAuth token"
        )

    return {"status": "success", "message": "OAuth token set successfully"}


@router.get("/projects")
async def get_projects():
    """Get all Jira projects"""
    try:
        projects = jira_service.get_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting projects: {str(e)}",
        )


@router.post("/search")
async def search_issues(query: JiraSearchQuery):
    """Search for Jira issues using JQL"""
    try:
        results = jira_service.search_issues(
            jql=query.jql, max_results=query.max_results, fields=query.fields
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching issues: {str(e)}",
        )


@router.post("/issues")
async def create_issue(issue: JiraIssueCreate):
    """Create a new Jira issue"""
    try:
        # Convert the issue model to format expected by the service
        additional_fields = issue.additional_fields or {}

        # Add any other fields that need to be passed to the API
        if issue.due_date:
            additional_fields["duedate"] = issue.due_date
        if issue.priority:
            additional_fields["priority"] = {"name": issue.priority}

        if issue.labels:
            additional_fields["labels"] = issue.labels

        result = jira_service.create_issue(
            project_key=issue.project_key,
            summary=issue.summary,
            description=issue.description or "",
            issue_type=issue.issue_type,
            assignee=issue.assignee,
            components=issue.components,
            additional_fields=additional_fields,
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating issue: {str(e)}",
        )


@router.get("/issues/{issue_key}")
async def get_issue(issue_key: str):
    """Get a Jira issue by key"""
    try:
        result = jira_service.get_issue(issue_key)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if "Issue does not exist" in str(e)
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=f"Error getting issue {issue_key}: {str(e)}",
        )


@router.put("/issues/{issue_key}")
async def update_issue(issue_key: str, issue_update: JiraIssueUpdate):
    """Update a Jira issue"""
    try:
        # Convert the update model to format expected by the API
        fields: Dict[str, Any] = {}

        if issue_update.summary:
            fields["summary"] = issue_update.summary

        if issue_update.description:
            fields["description"] = issue_update.description

        if issue_update.assignee:
            fields["assignee"] = issue_update.assignee

        # Add other fields from additional_fields
        if issue_update.additional_fields:
            fields.update(issue_update.additional_fields)

        # Handle specialized fields
        if issue_update.due_date:
            fields["duedate"] = issue_update.due_date

        if issue_update.priority:
            fields["priority"] = {"name": issue_update.priority}

        if issue_update.labels:
            fields["labels"] = issue_update.labels

        if issue_update.components:
            fields["components"] = [{"name": name} for name in issue_update.components]

        result = jira_service.update_issue(issue_key=issue_key, fields=fields)

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating issue {issue_key}: {str(e)}",
        )


@router.post("/issues/{issue_key}/comments")
async def add_comment(issue_key: str, comment: JiraComment):
    """Add a comment to a Jira issue"""
    try:
        result = jira_service.add_comment(issue_key=issue_key, comment=comment.body)

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding comment to issue {issue_key}: {str(e)}",
        )


@router.get("/issues/{issue_key}/transitions")
async def get_transitions(issue_key: str):
    """Get available transitions for a Jira issue"""
    try:
        transitions = jira_service.get_transitions(issue_key)
        return {"transitions": transitions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting transitions for issue {issue_key}: {str(e)}",
        )


@router.post("/issues/{issue_key}/transitions")
async def transition_issue(issue_key: str, transition: JiraTransition):
    """Transition a Jira issue to a new status"""
    try:
        result = jira_service.transition_issue(
            issue_key=issue_key,
            transition_id=transition.transition_id,
            comment=transition.comment,
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transitioning issue {issue_key}: {str(e)}",
        )


@router.get("/myself")
async def get_myself():
    """Get information about the current user"""
    try:
        result = jira_service.myself()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting current user: {str(e)}",
        )
