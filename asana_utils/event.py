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
