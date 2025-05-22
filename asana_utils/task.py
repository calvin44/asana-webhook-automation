from collections import defaultdict
from typing import Dict, List, Optional
from asana import TasksApi, AttachmentsApi, StoriesApi

from asana.rest import ApiException
from loguru import logger
from asana_utils.api import get_asana_client
from utils.resources import PROJECT_GID


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
        "added": defaultdict(list),
        "undeleted": defaultdict(list)
    }

    for event in events:
        resource = event.get("resource", {})
        action = event.get("action")

        if resource.get("resource_type") != "task":
            continue

        resource_gid = resource.get("gid")
        match action:
            case "changed":
                if resource_gid:
                    grouped_events["changed"][resource_gid].append(event)
                else:
                    logger.warning(
                        f"Missing 'gid' in 'changed' event: {event}")

            case "added":
                gid = resource_gid
                if resource["resource_type"] == "task" and event["parent"]["resource_type"] == "task":
                    gid = event.get("parent", {}).get("gid")
                grouped_events["added"][gid].append(event)
            case "undeleted":
                grouped_events["undeleted"][resource_gid].append(event)
            case _:
                logger.warning(
                    f"Unhandled event action: {action}, event: {event}")

    return {
        "changed": dict(grouped_events["changed"]),
        "added": dict(grouped_events["added"]),
        "undeleted": dict(grouped_events["undeleted"])
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
        "name"
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


def update_task(task_gid: str, update_data: Dict, opts: Dict = {}) -> None:  # pylint: disable=dangerous-default-value
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


def get_task_comments(task_gid: str) -> List[Dict]:
    """
    Fetches all comment stories for a given Asana task.
    """
    stories_api = StoriesApi(get_asana_client())
    opts = {"limit": 100}

    try:
        stories = list(stories_api.get_stories_for_task(task_gid, opts))
        logger.debug(f"Fetched stories for task {task_gid}: {stories}")

        # Only keep stories that are actual comments
        comment_infos = [
            story for story in stories
            if story.get("type") == "comment"
        ]

        return comment_infos

    except ApiException as e:
        logger.error(f"Error fetching stories for task {task_gid}: {e}")
        return []


def get_task_from_project(project_gid: str = PROJECT_GID, opts: Dict = {}):  # pylint: disable=dangerous-default-value
    """
    Get a list of tasks under a project
    """

    try:
        task_api = TasksApi(get_asana_client())
        task_list = list(task_api.get_tasks_for_project(project_gid, opts))
        return task_list

    except ApiException as e:
        logger.error(f"Error fetching task list: {e}")
        return []
