from typing import Dict, List
from loguru import logger


from scoring_system.add_new_company import append_new_company
from utils.notify import send_slack_notification

from asana_utils.custom_option import get_task_option
from asana_utils.event import has_add_event
from asana_utils.task import delete_task, get_task_attachments, get_task_info, update_task


def handle_requirement_clarifying(events_by_task: List[Dict]):
    """
    Process task events and delete task if request does not contain 'Decription' or attachement.
    """
    # return if there is no event to process
    if not events_by_task:
        logger.info(
            "[Handle Requirement Collection] ➡️ No events to process.")
        return

    for task_gid, task_events in events_by_task.items():
        # Skip tasks that have no change-related events
        if not has_add_event(task_events):
            logger.info(f"No add event for task {task_gid}.")
            continue

        logger.info(f"Processing task {task_gid} with events: {task_events}")

        # Fetch latest task info from Asana
        task_info = get_task_info(task_gid)
        if not task_info:
            logger.error(f"Failed to fetch task info for task {task_gid}")
            continue
        logger.info(f"Task info: {task_info}")

        # Only proceed if the task status is 'Requirement Clarifying'
        option = get_task_option(task_info)
        logger.info(f"Task option: {option}")
        if option["name"] != "Requirement Clarifying":
            logger.info(
                f"Task {task_gid} is not in 'Requirement Clarifying' status.")
            continue

        logger.info(f"Task {task_gid} is in 'Requirement Clarifying' status.")

        # Check if the task has a description or attachment
        attachments = get_task_attachments(task_gid)
        logger.info(f"Task attachments: {attachments}")

        # check description and attachemnt to determine whether request comes from form
        if task_info["notes"] and attachments:
            new_company_name = task_info["name"]
            append_new_company(new_company_name)
            logger.info(
                f"Task {task_gid} has a description and attachment. Confirmed request from form.")
            continue

        logger.info(
            f"Task {task_gid} does not have a description or attachment. Deleting task.")

        # Send notification on rule starting
        send_slack_notification(
            ":mailbox_with_ma il: *Requirement Clarifying* rule started")

        # Update task title to [Asana Rule Deleted Item]
        update_data = {"name": "[Asana Rule Deleted Item]"}
        update_task(task_gid, update_data)
        logger.info(
            f"Update task {task_gid} namet [Asana Rule Deleted Item] to handle undelete")

        # Delete the task
        delete_task(task_gid)

        # Send notification on rule starting
        send_slack_notification(
            f"🗑️ Task `{task_gid}` was deleted due to lack of information.")
