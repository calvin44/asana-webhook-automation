from typing import Dict, List
from gspread import Worksheet
from loguru import logger

from actions.pending_approval import has_change_in_enum_option_field
from asana_utils.custom_option import get_task_option
from asana_utils.event import has_change_event
from asana_utils.task import get_task_info
from scoring_system.g_sheet import get_sheet_client
from utils.notify import asana_slack_notification, notify_asana_failure
from utils.resources import SCORING_DOC_NAME, SCORING_SHEETNAME


def handle_project_status_updates(events_by_task: Dict[str, List[Dict]]) -> None:
    """
    Process Asana webhook events and update the Google Sheet project status
    when specific enum field changes are detected.

    Args:
        events_by_task (Dict[str, List[Dict]]): Mapping of task GID to event list.
    """
    if not events_by_task:
        logger.info("[Handle Project Status] No events to process.")
        return

    for task_gid, task_events in events_by_task.items():
        logger.info(f"📦 Processing task to update project status {task_gid}")

        if not has_change_event(task_events):
            logger.info(f"🔁 Skipping task {task_gid} - No new 'add' event.")
            continue

        task_info = get_task_info(task_gid)
        if not task_info:
            logger.error(f"⚠️ Failed to fetch task info for {task_gid}")
            continue

        company_name = task_info.get("name", "").strip()
        if not company_name:
            logger.warning(f"❓ No company name found for task {task_gid}")
            notify_asana_failure(
                task_gid, f"{company_name} is not found on Project Scoring Sheet. Update failed!")
            continue

        option = get_task_option(task_info)
        if not option:
            logger.info(f"⚠️ No enum option found for task {task_gid}")
            continue

        project_status = option["name"].strip()
        update_project_status_in_sheet(company_name, project_status)

        asana_slack_notification(
            task_gid,
            f"Updated {company_name}'s status to {project_status} in Project Scoring",
            "When project status in asana is changed update it to Project Scoring"
        )


def update_project_status_in_sheet(company_name: str, project_status: str) -> None:
    """
    Updates the 'Status' field in the scoring Google Sheet for a given company.

    Args:
        company_name (str): Company name to look up in the sheet.
        project_status (str): Status value to write (must match dropdown values).
    """
    logger.info(f"🚀 Updating status for '{company_name}' to '{project_status}'")

    try:
        client = get_sheet_client()
        spreadsheet = client.open(SCORING_DOC_NAME)
        sheet = spreadsheet.worksheet(SCORING_SHEETNAME)
    except Exception as e:
        logger.error(f"❌ Failed to open Google Sheet: {e}")
        return

    company_names = sheet.col_values(1)
    if company_name.strip() not in map(str.strip, company_names):
        logger.warning(f"❌ Company '{company_name}' not found in sheet.")
        return

    cell_info = find_cell_address_by_value(sheet, 1, company_name)
    if not cell_info["found"]:
        logger.warning(f"❌ Failed to locate row for '{company_name}'")
        return

    status_cell = f"B{cell_info['row_index']}"
    try:
        sheet.update(status_cell, [[project_status]])
        logger.success(f"✅ Updated '{company_name}' to '{project_status}' at {status_cell}")
    except Exception as e:
        logger.error(f"❌ Failed to update status for '{company_name}': {e}")


def find_cell_address_by_value(sheet: Worksheet, column_index: int, target_value: str) -> Dict:
    """
    Finds the cell address of the first cell in a column matching the given value.

    Args:
        sheet (Worksheet): The gspread worksheet object.
        column_index (int): 1-based column index (e.g. 1 = A).
        target_value (str): The value to search for.

    Returns:
        Dict: {
            "found": bool,
            "col_name": str,
            "row_index": int
        }
    """
    try:
        values = sheet.col_values(column_index)
        for row_index, val in enumerate(values, start=1):
            if val.strip() == target_value.strip():
                col_letter = chr(64 + column_index)
                return {
                    "found": True,
                    "col_name": col_letter,
                    "row_index": row_index
                }
    except Exception as e:
        logger.error(f"❌ Error finding value '{target_value}' in column {column_index}: {e}")

    return {"found": False}
