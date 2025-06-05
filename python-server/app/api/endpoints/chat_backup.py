"""Chat endpoint for Dialogflow-inspired conversational Jira interface."""

import logging
from typing import Any, Dict

from app.core.config import settings
from app.core.database import get_db
from app.schemas.api_schemas import ChatMessage, ChatResponse
from app.services.dialogflow_llm_service import DialogflowInspiredLLMService
from app.services.jira_user_lookup_service import JiraUserLookupService
from app.services.multi_user_jira_service import MultiUserJiraService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize LLM service
llm_service = DialogflowInspiredLLMService(
    openrouter_api_key=settings.OPENROUTER_API_KEY, model=settings.DEFAULT_LLM_MODEL
)


@router.post("/message/{user_id}", response_model=ChatResponse)
async def process_chat_message(
    user_id: str, message: ChatMessage, db: Session = Depends(get_db)
):
    """Process a chat message using Dialogflow-inspired intent classification.

    Flow:
    1. Classify intent (create, assign, query, etc.)
    2. Extract entities (issue keys, usernames, dates, etc.)
    3. Check if all required entities are present
    4. If missing entities: Ask clarification question
        5. If complete: Execute Jira action and respond
    """
    try:
        # Step 1: Process message through Dialogflow-inspired pipeline first
        llm_response = await llm_service.process_message(user_id, message.text)

        logger.info(
            f"Processed message for user {user_id}: " f"intent={llm_response['intent']}"
        )

        # Step 2: Check authentication only for Jira-related intents
        jira_intents = [
            "create_issue",
            "query_issues",
            "update_issue",
            "assign_issue",
            "transition_issue",
            "add_comment",
            "upload_attachment",
        ]
        requires_jira_auth = llm_response["intent"] in jira_intents

        multi_service = MultiUserJiraService(db)
        jira_service = multi_service.get_jira_service(user_id)

        # If user is not authenticated and this requires Jira, provide login message
        if requires_jira_auth and not jira_service:
            return ChatResponse(
                text="Please log in to JIRA first to use the chatbot " "features.",
                intent="authentication_required",
                entities={},
                confidence=1.0,
                requires_clarification=False,
                jira_action_result=None,
                context={},
            )

        # Step 3: If this is a fulfillment response with a Jira action,
        # execute it
        jira_result = None
        if (
            llm_response["response_type"] == "fulfillment"
            and "action" in llm_response["response"]
            and llm_response["response"]["action"]
            and llm_response["response"]["action"].get("type")
        ):
            # Execute Jira action (authentication already checked above)
            jira_result = await execute_jira_action(
                user_id, llm_response["response"]["action"], db, llm_service
            )

            # Update response with Jira result
            if jira_result and jira_result.get("success"):
                llm_response["response"]["text"] += f"\n\n??{jira_result['message']}"
                if "issue_key" in jira_result:
                    llm_response["response"]["text"] += f" ({jira_result['issue_key']})"
            elif jira_result and not jira_result.get("success"):
                llm_response["response"]["text"] += f"\n\n??{jira_result['message']}"

        return ChatResponse(
            text=llm_response["response"]["text"],
            intent=llm_response["intent"],
            entities=llm_response["entities"],
            confidence=llm_response["confidence"],
            requires_clarification=llm_response["response_type"] == "clarification",
            jira_action_result=jira_result,
            context=llm_response["context"],
        )

    except Exception as e:
        logger.error(f"Error processing chat message for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process message: {str(e)}"
        )


async def execute_jira_action(
    user_id: str,
    action: Dict[str, Any],
    db: Session,
    llm_service: DialogflowInspiredLLMService,
) -> Dict[str, Any]:
    """Execute the Jira action based on intent and entities"""

    try:
        jira_service = MultiUserJiraService(db)
        action_type = action.get("type")
        params = action.get("parameters", {})

        if action_type == "create_issue":
            return await create_issue_action(user_id, params, jira_service)
        elif action_type == "assign_issue":
            return await assign_issue_action(user_id, params, jira_service)
        elif action_type == "transition_issue":
            return await transition_issue_action(user_id, params, jira_service)
        elif action_type == "search_issues":
            return await search_issues_action(
                user_id, params, jira_service, llm_service
            )
        elif action_type == "add_comment":
            return await add_comment_action(user_id, params, jira_service)
        elif action_type == "update_issue":
            return await update_issue_action(user_id, params, jira_service)
        else:
            return {"success": False, "message": f"Unknown action type: {action_type}"}

    except Exception as e:
        logger.error(
            f"Error executing Jira action {action_type} for user {user_id}: {str(e)}"
        )
        return {"success": False, "message": f"Failed to execute action: {str(e)}"}


async def create_issue_action(
    user_id: str, params: Dict[str, Any], jira_service: MultiUserJiraService
) -> Dict[str, Any]:
    """Create a new Jira issue"""

    try:
        # Get user's default project if not specified
        project_key = params.get("project_key", settings.DEFAULT_JIRA_PROJECT_KEY)

        issue_data = {
            "project": {"key": project_key},
            "summary": params.get("summary", "New task from chatbot"),
            "description": params.get(
                "description", "Created via Jira Chatbot Extension"
            ),
            "issuetype": {"name": "Task"},
        }  # Add optional fields
        if "assignee" in params:
            # Remove @ symbol if present
            assignee_display_name = params["assignee"].lstrip("@")
            # Look up the user by display name to get the account ID
            jira_service_for_lookup = jira_service.get_jira_service(user_id)
            if jira_service_for_lookup:
                # Use JiraUserLookupService to find user by display name
                lookup_service = JiraUserLookupService(jira_service.db)
                user_info = lookup_service.find_user_by_display_name(
                    assignee_display_name, jira_service_for_lookup
                )
                if user_info and user_info.get("accountId"):
                    # Use accountId for Jira Cloud
                    issue_data["assignee"] = {"accountId": user_info["accountId"]}
                    logger.info(
                        f"Found assignee '{assignee_display_name}' with "
                        f"accountId: {user_info['accountId']}"
                    )
                else:
                    # Fallback to display name if user not found
                    logger.warning(
                        f"Could not find user with display name "
                        f"'{assignee_display_name}', using name fallback"
                    )
                    issue_data["assignee"] = {"name": assignee_display_name}
            else:
                # Fallback if no jira service available
                issue_data["assignee"] = {"name": assignee_display_name}

        if "priority" in params:
            priority_map = {
                "low": "Low",
                "medium": "Medium",
                "high": "High",
                "critical": "Critical",
                "urgent": "Highest",
            }
            priority = priority_map.get(params["priority"].lower(), "Medium")
            issue_data["priority"] = {"name": priority}

        if "due_date" in params:
            from datetime import datetime, timedelta

            due_date_str = params["due_date"].lower().strip()

            # Handle relative dates
            if due_date_str in ["today"]:
                due_date = datetime.now().strftime("%Y-%m-%d")
            elif due_date_str in ["tomorrow"]:
                due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif due_date_str in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]:
                # Calculate next occurrence of the specified day
                days_of_week = {
                    "monday": 0,
                    "tuesday": 1,
                    "wednesday": 2,
                    "thursday": 3,
                    "friday": 4,
                    "saturday": 5,
                    "sunday": 6,
                }
                target_day = days_of_week[due_date_str]
                current_day = datetime.now().weekday()
                days_ahead = target_day - current_day
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                due_date = (datetime.now() + timedelta(days=days_ahead)).strftime(
                    "%Y-%m-%d"
                )
            elif due_date_str == "next week":
                due_date = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
            elif due_date_str == "next month":
                due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            else:  # Assume it's already in YYYY-MM-DD format or try to parse it
                try:
                    datetime.strptime(due_date_str, "%Y-%m-%d")
                    due_date = due_date_str
                except ValueError:
                    # If parsing fails, skip due date
                    logger.warning(f"Could not parse due date: {due_date_str}")
                    due_date = None

            if due_date:
                issue_data["duedate"] = due_date

        # Create the issue
        result = await jira_service.create_issue(user_id, issue_data)

        if result["success"]:
            return {
                "success": True,
                "message": "Issue created successfully",
                "issue_key": result["issue"]["key"],
                "issue_url": f"{settings.JIRA_URL}/browse/{result['issue']['key']}",
            }
        else:
            return {"success": False, "message": result["error"]}

    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}")
        return {"success": False, "message": f"Failed to create issue: {str(e)}"}


async def assign_issue_action(
    user_id: str, params: Dict[str, Any], jira_service: MultiUserJiraService
) -> Dict[str, Any]:
    """Assign an issue to a user"""

    try:
        issue_key = params.get("issue_key")
        assignee = params.get("assignee", "").lstrip("@")

        if not issue_key or not assignee:
            return {"success": False, "message": "Missing issue key or assignee"}

        result = await jira_service.assign_issue(user_id, issue_key, assignee)

        if result["success"]:
            return {
                "success": True,
                "message": f"Assigned {issue_key} to {assignee}",
                "issue_key": issue_key,
            }
        else:
            return {"success": False, "message": result["error"]}

    except Exception as e:
        return {"success": False, "message": f"Failed to assign issue: {str(e)}"}


async def transition_issue_action(
    user_id: str, params: Dict[str, Any], jira_service: MultiUserJiraService
) -> Dict[str, Any]:
    """Transition an issue to a new status"""

    try:
        issue_key = params.get("issue_key")
        status = params.get("status")

        if not issue_key or not status:
            return {"success": False, "message": "Missing issue key or status"}

        # Map common status names
        status_map = {
            "todo": "To Do",
            "to do": "To Do",
            "in progress": "In Progress",
            "done": "Done",
            "completed": "Done",
            "closed": "Done",
        }

        mapped_status = status_map.get(status.lower(), status)

        result = await jira_service.transition_issue(user_id, issue_key, mapped_status)

        if result["success"]:
            return {
                "success": True,
                "message": f"Moved {issue_key} to {mapped_status}",
                "issue_key": issue_key,
            }
        else:
            return {"success": False, "message": result["error"]}

    except Exception as e:
        return {"success": False, "message": f"Failed to transition issue: {str(e)}"}


async def search_issues_action(
    user_id: str,
    params: Dict[str, Any],
    jira_service: MultiUserJiraService,
    llm_service: DialogflowInspiredLLMService,
) -> Dict[str, Any]:
    """Search for issues based on criteria with improved UX formatting and
    pagination support"""

    try:  # Get conversation context for pagination
        context = llm_service.get_conversation_context(user_id)

        # Check if this is a pagination request - use the context's pagination detection
        # We need to get the original message to check if it's a pagination request
        conversation_history = context.conversation_history
        last_user_message = ""
        if conversation_history:
            for msg in reversed(conversation_history):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break

        is_pagination = (
            context.is_pagination_request(last_user_message)
            and context.has_more_search_results()
            and len(context.last_search_results) > 0
        )

        if is_pagination:
            # Show next page of existing results
            page_issues, has_more = context.get_next_search_page()

            if not page_issues:
                return {
                    "success": True,
                    "message": "?? No more issues to show! You've seen all the results.",
                }

            # Format the pagination results
            total_count = len(context.last_search_results)
            display_count = len(page_issues)
            current_page_start = context.search_display_index - display_count
            # Header for pagination
            header = (
                f"<div style='margin-bottom: 16px; font-size: 16px; "
                f"font-weight: bold; color: #0052CC;'>?? Showing issues "
                f"{current_page_start + 1}-{current_page_start + display_count} "
                f"of {total_count}:</div>"
            )

        else:
            # New search - build JQL query from parameters
            jql_parts = []

            if "assignee" in params:
                assignee = params["assignee"].lstrip("@")
                jql_parts.append(f"assignee = '{assignee}'")

            if "project_key" in params:
                jql_parts.append(f"project = '{params['project_key']}'")

            if "status" in params:
                jql_parts.append(f"status = '{params['status']}'")

            jql = " AND ".join(jql_parts) if jql_parts else "assignee = currentUser()"

            result = await jira_service.search_issues(
                user_id, jql, max_results=50
            )  # Get more results for pagination
            if not result["success"]:
                return {"success": False, "message": result["error"]}

            all_issues = result["issues"]
            if not all_issues:
                # Clear any previous search state
                context.clear_search_state()
                return {
                    "success": True,
                    "message": "?? No open issues found! You're all caught up! ??",
                }

            # Store search results and parameters in context
            context.store_search_results(all_issues, params)

            # Get first page of results
            page_issues, has_more = context.get_next_search_page()

            total_count = len(all_issues)
            display_count = len(page_issues)  # Header for new search
            if total_count == 1:
                header = (
                    f"<div style='margin-bottom: 16px; font-size: 16px; "
                    f"font-weight: bold; color: #0052CC;'>?? Found "
                    f"{total_count} open issue:</div>"
                )
            else:
                header = (
                    f"<div style='margin-bottom: 16px; font-size: 16px; "
                    f"font-weight: bold; color: #0052CC;'>?? Found "
                    f"{total_count} open issues (showing first "
                    f"{display_count}):</div>"
                )

        # Format each issue with card-style layout (same formatting as before)
        formatted_issues = []
        for i, issue in enumerate(page_issues, 1):
            fields = issue["fields"]

            # Get issue metadata
            status = fields.get("status", {}).get("name", "Unknown")
            priority = fields.get("priority", {}).get("name", "Medium")
            assignee = (
                fields.get("assignee", {}).get("displayName", "Unassigned")
                if fields.get("assignee")
                else "Unassigned"
            )  # Status styling based on status
            status_styles = {
                "To Do": (
                    "background: #DEEBFF; color: #0747A6; padding: 4px 8px; "
                    "border-radius: 12px; font-size: 12px; font-weight: 500; "
                    "text-transform: uppercase;"
                ),
                "In Progress": (
                    "background: #E9F2E4; color: #216E4E; padding: 4px 8px; "
                    "border-radius: 12px; font-size: 12px; font-weight: 500; "
                    "text-transform: uppercase;"
                ),
                "Done": (
                    "background: #E3FCEF; color: #006644; padding: 4px 8px; "
                    "border-radius: 12px; font-size: 12px; font-weight: 500; "
                    "text-transform: uppercase;"
                ),
                "Closed": (
                    "background: #DFE1E6; color: #42526E; padding: 4px 8px; "
                    "border-radius: 12px; font-size: 12px; font-weight: 500; "
                    "text-transform: uppercase;"
                ),
                "Open": (
                    "background: #DEEBFF; color: #0747A6; padding: 4px 8px; "
                    "border-radius: 12px; font-size: 12px; font-weight: 500; "
                    "text-transform: uppercase;"
                ),
            }
            status_style = status_styles.get(status, status_styles["To Do"])

            # Priority emoji and color
            priority_colors = {
                "Highest": "#FF5630",
                "High": "#FF8B00",
                "Medium": "#FFAB00",
                "Low": "#36B37E",
                "Lowest": "#00B8D9",
            }
            priority_color = priority_colors.get(priority, priority_colors["Medium"])

            # Truncate summary if too long
            summary = fields["summary"]
            if len(summary) > 70:
                summary = summary[:67] + "..."

            # Create card-style HTML for each issue
            issue_card = f"""
                <div style='
                    background: white;
                    border: 1px solid #DFE1E6;
                    border-radius: 6px;
                    margin: 8px 0;
                    padding: 16px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    transition: all 0.2s ease;
                    border-left: 4px solid #0052CC;
                '>                    <div style='display: flex; justify-content: space-between;
                         align-items: center; margin-bottom: 8px;'>
                        <a href='{settings.JIRA_URL}/browse/{issue['key']}'
                           target='_blank'
                           style='
                               color: #0052CC;
                               text-decoration: none;
                               font-weight: 600;
                               font-size: 14px;
                               border: 1px solid #0052CC;
                               padding: 4px 8px;
                               border-radius: 3px;
                               background: rgba(0,82,204,0.1);
                           '
                           title='Click to open {issue['key']} in JIRA'
                        >{issue['key']}</a>
                        <span style='{status_style}'>{status}</span>
                    </div>
                    <div style='
                        font-size: 14px;
                        color: #172B4D;
                        margin-bottom: 12px;
                        line-height: 1.4;
                        font-weight: 500;
                    '>{summary}</div>
                    <div style='
                        display: flex;
                        gap: 16px;
                        font-size: 12px;
                        color: #6B778C;
                        align-items: center;
                    '>
                        <span>?�� {assignee}</span>
                        <span style='color: {priority_color}; font-weight: 500;'>?�� {priority}</span>
                        <span>?? {status}</span>
                    </div>
                </div>"""

            formatted_issues.append(issue_card)

        # Combine header and issues
        message = header + "".join(formatted_issues)

        # Add footer with pagination info
        if context.has_more_search_results():
            remaining = len(context.last_search_results) - context.search_display_index
            message += f"""
            <div style='
                margin-top: 16px;
                padding: 12px;
                background: #F4F5F7;
                border-radius: 6px;
                text-align: center;
                font-style: italic;
                color: #6B778C;
            '>
                ?? {remaining} more issues available. Say "show more issues" to see them.
            </div>"""  # Add helpful action suggestions
        message += """
        <div style='
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #0052CC 0%, #0747A6 100%);
            border-radius: 8px;
            color: white;
        '>
            <div style='font-weight: bold; margin-bottom: 8px;'>?�� Quick Actions:</div>
            <div style='font-size: 13px; line-height: 1.6;'>
                ??Say "create issue" to add a new one<br>
                ??Say "assign [issue-key] to [name]" to reassign<br>
                ??Say "move [issue-key] to done" to update status<br>
                ??Click any issue key above to open in JIRA
            </div>
        </div>"""

        return {"success": True, "message": message}

    except Exception as e:
        return {"success": False, "message": f"Failed to search issues: {str(e)}"}


async def add_comment_action(
    user_id: str, params: Dict[str, Any], jira_service: MultiUserJiraService
) -> Dict[str, Any]:
    """Add a comment to an issue"""

    try:
        issue_key = params.get("issue_key")
        comment = params.get("comment") or params.get("summary", "")

        if not issue_key or not comment:
            return {"success": False, "message": "Missing issue key or comment"}

        result = await jira_service.add_comment(user_id, issue_key, comment)

        if result["success"]:
            return {
                "success": True,
                "message": f"Added comment to {issue_key}",
                "issue_key": issue_key,
            }
        else:
            return {"success": False, "message": result["error"]}

    except Exception as e:
        return {"success": False, "message": f"Failed to add comment: {str(e)}"}


async def update_issue_action(
    user_id: str, params: Dict[str, Any], jira_service: MultiUserJiraService
) -> Dict[str, Any]:
    """Update an issue's fields (e.g., priority, summary, description)"""

    try:
        issue_key = params.get("issue_key")
        field = params.get("field")
        value = params.get("value")

        if not issue_key:
            return {"success": False, "message": "Missing issue key"}

        if not field or not value:
            return {"success": False, "message": "Missing field or value to update"}

        # Build the fields dictionary based on the field type
        fields = {}

        if field.lower() == "priority":
            # Map common priority values
            priority_map = {
                "low": "Low",
                "medium": "Medium",
                "high": "High",
                "critical": "Critical",
                "urgent": "Highest",
                "highest": "Highest",
                "lowest": "Lowest",
            }
            priority = priority_map.get(value.lower(), value)
            fields["priority"] = {"name": priority}

        elif field.lower() in ["summary", "title"]:
            fields["summary"] = value

        elif field.lower() == "description":
            fields["description"] = value

        elif field.lower() == "assignee":
            # Remove @ symbol if present
            assignee_display_name = value.lstrip("@")
            # Look up the user by display name to get the account ID
            jira_service_for_lookup = jira_service.get_jira_service(user_id)
            if jira_service_for_lookup:
                lookup_service = JiraUserLookupService(jira_service.db)
                user_info = lookup_service.find_user_by_display_name(
                    assignee_display_name, jira_service_for_lookup
                )
                if user_info and user_info.get("accountId"):
                    fields["assignee"] = {"accountId": user_info["accountId"]}
                else:
                    # Fallback to display name if user not found
                    fields["assignee"] = {"name": assignee_display_name}
            else:
                fields["assignee"] = {"name": assignee_display_name}

        else:
            # For other fields, try direct assignment
            fields[field] = value

        # Update the issue using the multi-user service
        jira_service_instance = jira_service.get_jira_service(user_id)
        if not jira_service_instance:
            return {"success": False, "message": "User not authenticated"}

        result = jira_service_instance.update_issue(issue_key, fields)

        if result:
            return {
                "success": True,
                "message": f"Updated {field} for {issue_key} to '{value}'",
                "issue_key": issue_key,
            }
        else:
            return {"success": False, "message": f"Failed to update {issue_key}"}

    except Exception as e:
        logger.error(f"Error updating issue: {str(e)}")
        return {"success": False, "message": f"Failed to update issue: {str(e)}"}
