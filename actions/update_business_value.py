from typing import Optional, Dict
from loguru import logger

from asana_utils.custom_option import get_custom_field
from asana_utils.task import get_task_from_project, get_task_info, update_task
from utils.notify import asana_slack_notification


def update_business_value_from_scoring(company_name: str, business_value: float) -> Dict[str, str]:
    """
    Updates the 'Business Value' custom field for a task in Asana that matches the given company name.

    This function:
    - Searches for a task in Asana by its name (assumed to be the company name).
    - Retrieves the task's detailed information.
    - Finds the 'Business Value' custom field.
    - Updates the task with the new business value.

    Args:
        company_name (str): The name of the company to match with a task in Asana.
        business_value (float): The numeric business value to set.

    Returns:
        dict: A status message indicating success or a specific error cause.
    """
    logger.info(
        f"Updating business value for '{company_name}' to {business_value}")

    task_list = get_task_from_project()
    if not task_list:
        logger.exception("Failed to fetch task list from project")
        return {"status": "error", "message": "Failed to fetch task list"}

    matched_task: Optional[Dict] = next(
        (task for task in task_list if task.get("name") == company_name), None
    )
    if not matched_task:
        logger.warning(f"No task found with name '{company_name}'")
        return {"status": "error", "message": f"No task found for '{company_name}'"}

    task_info = get_task_info(matched_task["gid"])
    if not task_info:
        logger.exception(
            f"Failed to fetch detailed info for task '{company_name}'")
        return {"status": "error", "message": "Failed to fetch task info"}

    business_value_field = get_custom_field("Business Value", task_info)
    if not business_value_field or "gid" not in business_value_field:
        logger.exception("Failed to resolve 'Business Value' custom field")
        return {"status": "error", "message": "Custom field lookup failed"}

    try:
        update_data = {
            "custom_fields": {
                business_value_field["gid"]: business_value
            }
        }
        update_task(matched_task["gid"], update_data)
        logger.success(f"Business value updated for '{company_name}'")

        asana_slack_notification(
            matched_task["gid"],
            "Update business value to Asana",
            "Pulled business value from \"Project Scoring Google Sheet\""
        )

        return {"status": "success", "message": f"Business value updated for '{company_name}'"}
    except Exception as e:  # pylint: disable=broad-except
        logger.exception(f"Failed to update task '{company_name}'")
        return {"status": "error", "message": "Failed to update task", "detail": str(e)}
