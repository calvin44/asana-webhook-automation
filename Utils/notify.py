import requests
from loguru import logger

from Utils.resources import SLACK_WEBHOOK_URL


def notify_asana_failure(task_gid: str, reason: str, rule: str) -> None:
    """
    Sends a Slack notification when an Asana operation fails.

    Args:
        task_gid (str): The GID of the Asana task related to the failure.
        reason (str): Description of why the operation failed.
        rule (str): The rule name or identifier that is executing when the failure occurred.
    """
    task_url = f"https://app.asana.com/0/0/{task_gid}/f"
    message = (
        f"🚨 *Asana Error Notification*\n"
        f"*Rule:* {rule}\n"
        f"*Reason:* {reason}\n"
        f"*Task:* {task_url}"
    )

    payload = {
        "Message": message
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("✅ Slack notification sent successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send Slack notification: {e}")
