from typing import Dict, Optional


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
