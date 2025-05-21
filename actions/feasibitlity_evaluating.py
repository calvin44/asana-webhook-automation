from typing import Dict, List

from loguru import logger

from utils.notify import asana_slack_notification
from utils.role import project_managers

from asana_utils.enum_option import get_option_info
from asana_utils.event import has_change_event
from asana_utils.task import get_task_attachments, get_task_comments, update_task
from asana_utils.user import find_user_by_gid


def handle_feasibility_evaluating(events_by_task: List[Dict]) -> None:
    """
    When assignee set to PM (Lee/Lana), check if task has attachments or comments.
    if yes: Update enum_option to "Feasibility Evaluating"
    """

    # return if there is no event to process
    if not events_by_task:
        logger.info(
            "[Feasibility Evaluating] ➡️ No events to process.")
        return

    for task_gid, task_events in events_by_task.items():
        # Skip tasks that have no change-related events
        if not has_change_event(task_events):
            logger.info(f"No change event for task {task_gid}.")
            continue
        # Skip tasks that did not has assignee change
        asssignee_changes = get_assignee_change_event(task_events)
        logger.info(
            f"Assignee changes: {asssignee_changes}")

        if not asssignee_changes:
            logger.info("No assignee change from event")
            continue

        asana_slack_notification(
            task_gid,
            "Set option to \"Feasibility Evaluating\"",
            "When assignee is set to PM, set status to \"Feasibility Evaluating\" if there is attachment or comment"
        )

        handle_assignee_change(task_gid, asssignee_changes)


def get_assignee_change_event(task_events: List[Dict]) -> List[Dict]:
    """
    Check if the events contain an assignee change.
    """
    logger.info(f"Checking for assignee change in task events: {task_events}")

    assignee_changes = []
    for event in task_events:
        if (
            event.get("action") == "changed" and
            event.get("change", {}).get("field") == "assignee"
        ):
            assignee_changes.append(event["change"])
    return assignee_changes


def handle_assignee_change(task_gid: str, assignee_events: List[Dict]) -> None:
    """
    Handle the assignee change events for a task.
    """
    for change in assignee_events:
        new_value = change.get("new_value")
        logger.debug(f"change object: {change}")
        logger.debug(f"new_value: {new_value}")

        if new_value is None:
            logger.info(f"Assignee removed from task {task_gid}")
            continue

        new_assignee_gid = new_value.get("gid")
        if not new_assignee_gid:
            logger.warning(f"No 'gid' found in new_value: {new_value}")
            continue

        # Check if the new assignee is Lee or Lana
        user_info = find_user_by_gid(new_assignee_gid)
        logger.info(f"New assignee for task {task_gid}: {user_info}")
        if user_info["name"] not in project_managers:
            continue

        # Update enum_optioon to "Feasibility Evaluating if there is attachment or comment"
        task_comments = get_task_comments(task_gid)
        attachments = get_task_attachments(task_gid)
        logger.debug(f"task comment extracted: {task_comments}")
        if not task_comments or not attachments:
            logger.info(f"No task comment found in the task {task_gid}")
            continue

        # if there is attachemtns and comment means it is ready to be possed to PM
        # Update enum_option to feasibility Evaluating
        feasibility_evaluating_gid = get_option_info("Feasibility Evaluating")

        update_data = {
            "custom_type_status_option": feasibility_evaluating_gid
        }
        update_task(task_gid, update_data)
        logger.debug(f"option gid: {feasibility_evaluating_gid}")
