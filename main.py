"""
Asana Webhook Processor

A FastAPI application that handles Asana webhooks and processes task events.
Includes background task processing for various Asana task states.
"""

from contextlib import asynccontextmanager
from typing import Dict, List
import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request, Header, Response, Depends
from loguru import logger
from pydantic import BaseModel

from asana_utils.task import group_events_by_task_gid
from utils.resources import ASANA_PAT
from utils.webhook import check_webhook_exists
from scoring_system.add_new_company import append_new_company
from actions.feasibitlity_evaluating import handle_feasibility_evaluating
from actions.force_delete import force_delete_undeleted
from actions.pending_approval import handle_pending_approval
from actions.requirement_clarifying import handle_requirement_clarifying

# ======================
# Configuration
# ======================


class Settings:
    """Application configuration settings."""
    WEBHOOK_SECRET = ASANA_PAT  # Move to environment variables in production
    PORT = 5000
    RELOAD = True

# ======================
# Data Models
# ======================


class WebhookPayload(BaseModel):
    """Pydantic model for validating Asana webhook payload."""
    events: List[Dict]

# ======================
# Dependencies
# ======================


async def verify_webhook_secret(x_hook_secret: str = Header(default=None)):
    """
    Verify the webhook secret header.

    Args:
        x_hook_secret: The secret token from Asana webhook header

    Returns:
        Response: 403 if invalid, otherwise passes through
    """
    if x_hook_secret and x_hook_secret != Settings.WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret attempt")
        return Response(status_code=403)
    return x_hook_secret

# ======================
# FastAPI App
# ======================


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Manage FastAPI application lifecycle events.

    On startup:
    - Verifies Asana webhook exists
    On shutdown:
    - Logs shutdown message
    """
    if not check_webhook_exists():
        logger.warning("Webhook not found. Please create one...")
    else:
        logger.info("Webhook already exists in Asana.")
    yield
    logger.info("🛑 Application is shutting down...")

app = FastAPI(
    lifespan=lifespan,
    title="Asana Webhook Processor",
    description="Handles Asana webhooks and processes task events"
)

# ======================
# Routes
# ======================


@app.get("/")
async def health_check():
    """Health check endpoint for service monitoring."""
    return {"status": "running"}


@app.get("/test")
async def test_endpoint():
    """
    Temporary testing endpoint.

    Note:
        Remove this in production environments.
    """
    append_new_company("New Company")
    return {"message": "Test completed"}


@app.post("/asana-webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hook_secret: str = Depends(verify_webhook_secret)
):
    """
    Process incoming Asana webhook events.

    Args:
        request: The incoming request object
        background_tasks: FastAPI background tasks handler
        x_hook_secret: Webhook verification secret

    Returns:
        dict: Processing status or error message
    """
    # Webhook handshake
    if x_hook_secret:
        return Response(headers={"X-Hook-Secret": x_hook_secret})

    try:
        payload = WebhookPayload.model_validate(await request.json())
        events_by_task = group_events_by_task_gid(payload.events)

        # Process events in background
        background_tasks.add_task(
            handle_pending_approval, events_by_task["changed"])
        background_tasks.add_task(
            handle_feasibility_evaluating, events_by_task["changed"])
        background_tasks.add_task(
            handle_requirement_clarifying, events_by_task["added"])
        background_tasks.add_task(
            force_delete_undeleted, events_by_task["undeleted"])

        return {"status": "processing_started"}

    except Exception as e:  # pylint: disable=broad-except
        logger.exception(f"Webhook processing failed: {e}")
        return {"status": "error", "message": str(e)}

# ======================
# Main
# ======================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=Settings.PORT,
        reload=Settings.RELOAD
    )
