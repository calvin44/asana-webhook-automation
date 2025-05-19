from collections import defaultdict
from typing import Dict, List, Optional
from asana import TasksApi, AttachmentsApi

from asana.rest import ApiException
from loguru import logger
from asana_utils.api import get_asana_client


def group_events_by_task_gid(events: List[Dict]) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Groups Asana webhook events by action type and then by task GID.

    Returns:
        A nested dictionary structured as:
        {
            "changed": {task_gid: [event, ...]},
            "added": {parent_gid: [event, ...]},
        }
    """
    grouped_events: Dict[str, Dict[str, List[Dict]]] = {
        "changed": defaultdict(list),
        "added": defaultdict(list)
    }

    for event in events:
        resource = event.get("resource", {})
        action = event.get("action")

        if resource.get("resource_type") != "task":
            continue

        match action:
            case "changed":
                task_gid = resource.get("gid")
                if task_gid:
                    grouped_events["changed"][task_gid].append(event)
                else:
                    logger.warning(
                        f"Missing 'gid' in 'changed' event: {event}")

            case "added":
                gid = resource.get("gid")
                if resource["resource_type"] == "task" and event["parent"]["resource_type"] == "task":
                    gid = event.get("parent", {}).get("gid")
                grouped_events["added"][gid].append(event)

            case _:
                logger.warning(
                    f"Unhandled event action: {action}, event: {event}")

    return {
        "changed": dict(grouped_events["changed"]),
        "added": dict(grouped_events["added"])
    }


def get_task_info(task_gid: str) -> Optional[Dict]:
    """
    Retrieve task information from Asana API.

    Args:
        task_gid: The GID of the task.

    Returns:
        Task information dictionary if successful, else None.
    """
    task_api = TasksApi(get_asana_client())

    fields = [
        "custom_type_status_option",
        "custom_fields.name",
        "custom_fields.display_value",
        "notes",
    ]

    opts = {"opt_fields": ",".join(fields)}

    try:
        return task_api.get_task(task_gid, opts)
    except ApiException as e:
        logger.error(f"Error fetching task {task_gid}: {e}")
        return None


def get_task_attachments(task_gid: str) -> List[Dict]:
    """
    Retrieve task attachments from Asana API.

    Args:
        task_gid: The GID of the task.

    Returns:
        A list of attachment dictionaries if successful, else an empty list.
    """
    attachment_api = AttachmentsApi(get_asana_client())

    try:
        attachments = list(
            attachment_api.get_attachments_for_object(task_gid, {}))
        logger.info(
            f"✅ Retrieved {len(attachments)} attachment(s) for task {task_gid}")
        return attachments

    except ApiException as e:
        logger.error(f"❌ Error fetching attachments for task {task_gid}: {e}")
        return []


def delete_task(task_gid: str) -> None:
    """
    Delete a task in Asana.

    Args:
        task_gid: The GID of the task to delete.
    """
    task_api = TasksApi(get_asana_client())
    try:
        task_api.delete_task(task_gid)
        logger.info(f"Task {task_gid} deleted successfully.")
    except ApiException as e:
        logger.error(f"Error deleting task {task_gid}: {e}")
