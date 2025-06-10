from typing import Dict, List


def has_change_event(events: List[Dict]) -> bool:
    """
    Check if any event in the list has action 'changed'.

    Returns:
        True if a change event is present, else False.
    """
    return any(event.get("action") == "changed" for event in events)


def has_add_event(events: List[Dict]) -> bool:
    """
    Check if any event in the list has action 'added'.

    Returns:
        True if a change event is present, else False.
    """
    return any(event.get("action") == "added" for event in events)

def is_child_of_project(events: List[Dict]) -> bool:
    """
    Check if the added task is a direct child of a project.
    Returns True if the task's parent is a section (i.e. direct child of project),
    and False if it's a subtask of another task or has no parent.
    """
    for event in events:
        if event.get('action') == 'added' and event.get('resource', {}).get('resource_type') == 'task':
            parent = event.get('parent')
            if parent and parent.get('resource_type') == 'section':
                return True
    return False
