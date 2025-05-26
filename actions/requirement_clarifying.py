from typing import Dict, List
from loguru import logger

from scoring_system.add_new_company import append_new_company
from utils.notify import asana_slack_notification, send_slack_notification

from asana_utils.custom_option import get_task_option
from asana_utils.event import has_add_event
from asana_utils.task import (
    delete_task,
    get_task_attachments,
    get_task_info,
    update_task,
)


def handle_requirement_clarifying(events_by_task: Dict[str, List[Dict]]):
    """
    Process task events and delete task if it lacks a description or attachment.
    """

    if not events_by_task:
        logger.info("[Handle Requirement Clarifying] ➡️ No events to process.")
        return

    for task_gid, task_events in events_by_task.items():
        if not has_add_event(task_events):
            logger.info(f"Skipping task {task_gid}: No 'add' event.")
            continue

        logger.info(f"Processing task {task_gid}...")

        task_info = get_task_info(task_gid)
        if not task_info:
            logger.error(f"Failed to fetch task info for {task_gid}")
            continue

        option = get_task_option(task_info)
        if option.get("name") != "Requirement Clarifying":
            logger.info(f"Task {task_gid} is not in 'Requirement Clarifying' status.")
            continue

        logger.info(f"Task {task_gid} is in 'Requirement Clarifying' status.")

        attachments = get_task_attachments(task_gid)
        has_description = bool(task_info.get("notes"))
        has_attachments = bool(attachments)

        if has_description and has_attachments:
            company_name = task_info.get("name")
            if not company_name:
                logger.warning(f"Task {task_gid} is missing a company name.")
                continue

            append_new_company(company_name)

            asana_slack_notification(
                task_gid,
                "Add a new task to Project Scoring",
                "Added a new task to Project Scoring Board"
            )
            logger.info(f"Task {task_gid} is a valid request from form.")
            continue

        # Handle invalid task
        logger.info(f"Task {task_gid} lacks description or attachment. Deleting...")

        send_slack_notification(":mailbox_with_mail: *Requirement Clarifying* rule started")

        update_task(task_gid, {"name": "[Asana Rule Deleted Item]"})
        logger.info(f"Updated task {task_gid} name to '[Asana Rule Deleted Item]'")

        delete_task(task_gid)
        send_slack_notification(f"🗑️ Task `{task_gid}` was deleted due to lack of information.")
