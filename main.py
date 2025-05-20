from contextlib import asynccontextmanager

import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request, Header, Response
from loguru import logger

from actions.force_delete import force_delete_undeleted
from utils.webhook import check_webhook_exists
from actions.feasibitlity_evaluating import handle_requirement_clarifying
from actions.pending_approval import handle_pending_approval
from actions.requirement_collection import handle_requirement_collection
from asana_utils.task import group_events_by_task_gid

# Initialize FastAPI app with lifespan event


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Application startup and shutdown events.
    Checks for Asana webhook existence on startup.
    """
    if not check_webhook_exists():
        logger.warning("Webhook not found. Please create one...")
    else:
        logger.info("Webhook already exists in Asana.")
    yield
    logger.info("🛑 Application is shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {"message": "Asana Webhook Server is running!"}


@app.post("/asana-webhook")
async def handle_asana_webhook(
    request: Request,
    x_hook_secret: str = Header(default=None),
    background_tasks: BackgroundTasks = None,
):
    """
    Handles Asana webhook POST request.

    Args:
        request (Request): Incoming request from Asana.
        x_hook_secret (str): Secret header for webhook handshake.
        background_tasks (BackgroundTasks): Background task handler.

    Returns:
        JSON response indicating processing result.
    """
    if x_hook_secret:
        logger.info(f"🔐 Handshake secret received: {x_hook_secret}")
        return Response(status_code=200, headers={"X-Hook-Secret": x_hook_secret})

    try:
        payload = await request.json()
        logger.debug(f"📦 Webhook payload received: {payload}")

        events = payload.get("events", [])
        if not events:
            logger.warning("Received webhook with no events.")
            return {"status": "ignored", "reason": "No events in payload"}

        # Group events by task GID so we can process each task individually
        events_by_task = group_events_by_task_gid(events)
        logger.info(
            f"Grouped events by task GID: {events_by_task}")

        # Rule 0: Force delete undeleted items when title matched
        background_tasks.add_task(
            force_delete_undeleted, events_by_task["undeleted"])

        # Rule 1: Handle "Pending Approval"
        # When option is set to "Pending Approval"
        # 1. Set due date to 2 weeks from now
        # 2. Set assignee to "Sales Owner"
        background_tasks.add_task(
            handle_pending_approval, events_by_task["changed"])

        # Rule 2: Handle "Requirement Collection should come from form"
        # When a task is created:
        # 1. Check "Decritption" and "Attachement". If they are empty, delete the task
        background_tasks.add_task(
            handle_requirement_collection, events_by_task["added"])

        # Rule 3: When assignee set to PM (Lee/Lana), check if task has attachements or comments
        # if yes: Update enum_option to  "Feasibility Evaluating"
        # if no: do nothing / set to "Requirement Clarifying"
        background_tasks.add_task(
            handle_requirement_clarifying, events_by_task["changed"])

        logger.info(
            "Processed events: complete")

        return {"status": "received"}

    except Exception as e:  # pylint: disable=broad-except
        logger.exception(f"❌ Error processing webhook payload: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
