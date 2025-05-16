from collections import defaultdict
from typing import Dict, List


def group_events_by_task_gid(events: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Groups Asana webhook events by their task GID.

    Returns:
        A dictionary where keys are task GIDs and values are lists of events,
        assuming the input order is chronological.
    """
    grouped_events: Dict[str, List[Dict]] = defaultdict(list)

    for event in events:
        resource = event.get("resource", {})
        if resource.get("resource_type") != "task":
            continue
        task_id = resource.get("gid")
        if task_id:
            grouped_events[task_id].append(event)

    return dict(grouped_events)
