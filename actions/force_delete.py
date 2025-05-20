from typing import Dict, List

from loguru import logger

from utils.notify import asana_slack_notification
from asana_utils.task import delete_task, get_task_info


def force_delete_undeleted(events_by_task: List[Dict]):
    """
    Upon receiving undelete event
    Check for the title [Asana Rule Deleted Item]
    if title matched, force delete it
    """
    if not events_by_task:
        logger.info("[Force Delete] ➡️ No events to process.")
        return

    for task_gid, _ in events_by_task.items():
        logger.debug(f"Event by task: {task_gid}")
        task_info = get_task_info(task_gid)

        logger.info(f"Query task info: {task_info}")

        if task_info["name"] != "[Asana Rule Deleted Item]":
            continue

        asana_slack_notification(
            task_gid,
            "Prevent \"Undelete\" from user",
            "When user tries to undelete task delete it again"
        )

        delete_task(task_gid)
