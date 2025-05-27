"""
Asana Webhook Processor

A FastAPI application that handles Asana webhooks and processes task events.
Includes background task processing for various Asana task states.
"""

from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request, Header, Response, Depends
from loguru import logger
from pydantic import BaseModel, ValidationError

from asana_utils.task import group_events_by_task_gid
from scoring_system.add_new_company import append_new_company
from utils.resources import ASANA_PAT
from utils.webhook import check_webhook_exists

from actions.update_business_value import update_business_value_from_scoring
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


class UpdateBusinessValueWebhoook(BaseModel):
    """Pydantic model for validating Business value update webhook payload."""
    companyName: str
    businessValue: str | float

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

@app.post("/update-company-business-value")
async def handle_update_company_business_value(request: Request):
    """
    Webhook endpoint to update the Business Value of a company in Asana,
    triggered from Google Apps Script integrated with Google Sheets.
    """
    try:
        try:
            payload = UpdateBusinessValueWebhoook.model_validate(await request.json())
        except ValidationError as ve:
            logger.warning(f"Invalid payload format: {ve}")
            return {
                "status": "error",
                "message": "Invalid payload format",
                "detail": str(ve)
            }

        company_name = payload.companyName
        business_value_raw = payload.businessValue

        try:
            business_value = float(business_value_raw)
        except (ValueError, TypeError):
            return {
                "status": "error",
                "message": f"Invalid business value: '{business_value_raw}' is not a number"
            }

        update_business_value_from_scoring(company_name, business_value)

        return {
            "status": "success",
            "data": {
                "companyName": company_name,
                "businessValue": business_value
            }
        }

    except Exception as e:  # pylint: disable=broad-except
        logger.exception(f"Webhook processing failed: {e}")
        return {
            "status": "error",
            "message": "Internal server error",
            "detail": str(e)
        }


@app.post("/asana-webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hook_secret: Optional[str] = Header(None),
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
        return Response(content="", status_code=200, headers={"X-Hook-Secret": x_hook_secret})

    try:
        payload = WebhookPayload.model_validate(await request.json())
        logger.debug(f"Received Events: {payload}")
        events_by_task = group_events_by_task_gid(payload.events)
        logger.debug(f"Grouped Tasks: {events_by_task}")

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
