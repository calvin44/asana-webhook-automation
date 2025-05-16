from datetime import datetime, timedelta
from typing import List, Dict, Optional

from asana import TasksApi, UsersApi
from asana.rest import ApiException
from loguru import logger

from Utils.notify import notify_asana_failure
from Utils.resources import WORKSPACE_GID
from asana_utils.api import get_asana_client, get_enum_custom_fields
from asana_utils.task import group_events_by_task_gid


def handle_pending_approval(events: List[Dict]) -> None:
    """
    Process task events and update tasks with status 'Pending Approval'
    by setting due date and assignee based on 'Sales Owner' custom field.
    """

    # Group events by task GID so we can process each task individually
    events_by_task = group_events_by_task_gid(events)

    for task_gid, task_events in events_by_task.items():
        # Skip tasks that have no change-related events
        if not has_change_event(task_events):
            logger.info(f"No change event for task {task_gid}.")
            continue

        # Skip tasks that did not change the specific enum option (e.g., status field)
        if not has_change_in_enum_option_field(task_events):
            logger.info(f"No change in enum option for task {task_gid}.")
            continue

        # Fetch latest task info from Asana
        task_info = get_task_info(task_gid)
        if not task_info:
            logger.error(f"Failed to fetch task info for task {task_gid}")
            continue

        # Only proceed if the task status is 'Pending Approval'
        option = get_task_option(task_info)
        if option.get("name") != "Pending Approval":
            logger.info(
                f"Task {task_gid} is not in 'Pending Approval' status.")
            continue

        # Retrieve the 'Sales Owner' custom field from the task
        sales_owner_field = get_custom_field("Sales Owner", task_info)
        if not sales_owner_field:
            logger.error(f"'Sales Owner' field not found in task {task_gid}")
            continue

        logger.info(f"Sales owner field: {sales_owner_field}")

        # Try to find the user info by the name in the 'Sales Owner' field
        sales_account_info = find_user_by_name(
            sales_owner_field.get("display_value"))

        assigned_user_gid = None
        if not sales_account_info:
            # If user not found, log warning and proceed with due date only
            logger.error(
                f"Sales account info not found for '{sales_owner_field.get('display_value')}'")
            notify_asana_failure(
                task_gid, f"Sales account info not found for '{sales_owner_field.get('display_value')}', unassign Task assignee", "Pending Approval")
        else:
            # If found, include assignee in the update payload
            logger.info(f"Sales account info: {sales_account_info}")
            assigned_user_gid = sales_account_info["gid"]

        # Prepare task update payload with due date set to two weeks from now
        update_data = {
            "due_on": get_due_date_two_weeks_from_now(),
            "assignee": assigned_user_gid
        }

        # Define fields to include in the response (optional)
        opts = {"opt_fields": "assignee,due_on"}

        logger.info(f"Updating task {task_gid} with data: {update_data}")

        # Send update to Asana
        update_task(task_gid, update_data, opts)


def has_change_in_enum_option_field(events: List[Dict]) -> bool:
    """
    Check if any of the given events represent a change in the enum option field.

    This function compares the new enum_value GIDs in the events against the known
    enum options retrieved from the Asana custom field.

    Args:
        events (List[Dict]): A list of event dictionaries from the webhook payload.

    Returns:
        bool: True if any event includes a change to a known enum option, False otherwise.
    """
    enum_options = get_enum_custom_fields()
    for event in events:
        try:
            new_value_gid = (
                event.get("change", {})
                     .get("new_value", {})
                     .get("enum_value", {})
                     .get("gid")
            )
            if new_value_gid and new_value_gid in enum_options:
                return True
        except Exception as e:  # pylint: disable=broad-except
            logger.warning(f"Error parsing event: {event} | Exception: {e}")
            continue

    return False


def has_change_event(events: List[Dict]) -> bool:
    """
    Check if any event in the list has action 'changed'.

    Returns:
        True if a change event is present, else False.
    """
    return any(event.get("action") == "changed" for event in events)


def get_task_info(task_gid: str) -> Optional[Dict]:
    """
    Retrieve task information from Asana API.

    Args:
        task_gid: The GID of the task.

    Returns:
        Task information dictionary if successful, else None.
    """
    task_api = TasksApi(get_asana_client())
    opts = {"opt_fields": "custom_type_status_option,custom_fields.name,custom_fields.display_value"}

    try:
        return task_api.get_task(task_gid, opts)
    except ApiException as e:
        logger.error(f"Error fetching task {task_gid}: {e}")
        return None


def get_task_option(task_info: Dict) -> Dict:
    """
    Extract the 'custom_type_status_option' from task info.

    Args:
        task_info: The task information dictionary.

    Returns:
        Dictionary representing the status option or empty dict.
    """
    return task_info.get("custom_type_status_option", {})


def get_custom_field(field_name: str, task_info: Dict) -> Optional[Dict]:
    """
    Find a custom field by name in the task info.

    Args:
        field_name: Name of the custom field.
        task_info: Task information dictionary.

    Returns:
        The custom field dictionary if found, else None.
    """
    for field in task_info.get("custom_fields", []):
        if field.get("name") == field_name:
            return field
    return None


def update_task(task_gid: str, update_data: Dict, opts: Dict) -> None:
    """
    Update the task with provided data.

    Args:
        task_gid: The GID of the task to update.
        update_data: Dictionary of fields to update.
        opts: Additional options for the API call.
    """
    task_api = TasksApi(get_asana_client())
    body = {"data": update_data}

    try:
        response = task_api.update_task(body, task_gid, opts)
        logger.info(f"Task {task_gid} updated successfully: {response}")
    except ApiException as e:
        logger.error(f"Error updating task {task_gid}: {e}")


def get_due_date_two_weeks_from_now() -> str:
    """
    Get the date two weeks from now formatted as 'YYYY-MM-DD'.

    Returns:
        A string representing the due date.
    """
    two_weeks_later = datetime.utcnow() + timedelta(weeks=2)
    return two_weeks_later.strftime("%Y-%m-%d")


def find_user_by_name(name: Optional[str]) -> Optional[Dict]:
    """
    Search for a user by name in the workspace.

    Args:
        name: The name of the user to find.

    Returns:
        The user dictionary if found, else None.
    """
    if not name:
        return None

    user_api = UsersApi(get_asana_client())
    opts = {"workspace": WORKSPACE_GID,
            "limit": 100, "opt_fields": "name,email"}

    try:
        users = list(user_api.get_users(opts))
        for user in users:
            if user.get("name") == name:
                return user
        return None
    except ApiException as e:
        logger.error(f"Error fetching users: {e}")
        return None
