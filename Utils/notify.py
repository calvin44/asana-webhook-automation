import requests
from loguru import logger

from utils.resources import SLACK_WEBHOOK_URL


def generate_asana_url(task_gid):
    """
    Generate clickable url from task gid
    """
    return f"https://app.asana.com/0/0/{task_gid}/f"


def notify_asana_failure(task_gid: str, reason: str, rule: str) -> None:
    """
    Sends a Slack notification when an Asana operation fails.

    Args:
        task_gid (str): The GID of the Asana task related to the failure.
        reason (str): Description of why the operation failed.
        rule (str): The rule name or identifier that is executing when the failure occurred.
    """
    task_url = generate_asana_url(task_gid)
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


def asana_slack_notification(task_gid: str, action: str, rule: str) -> None:
    """
    Sends a Slack notification when an Asana operation fails.

    Args:
        task_gid (str): The GID of the Asana task related to the failure.
        reason (str): Description of why the operation failed.
        rule (str): The rule name or identifier that is executing when the failure occurred.
    """
    task_url = generate_asana_url(task_gid)
    message = (
        f":mailbox_with_mail:  *Asana Notification*\n"
        f"*Rule:* {rule}\n"
        f"*Action:* {action}\n"
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


def send_slack_notification(message: str) -> None:
    """
    Sends a Slack notification with the given message.

    Args:
        message (str): The message to send to Slack.
    """
    payload = {
        "Message": message
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("✅ Slack notification sent successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send Slack notification: {e}")
