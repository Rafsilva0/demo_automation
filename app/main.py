"""FastAPI application for Ada agent provisioning automation."""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.responses import JSONResponse
import structlog
from typing import Annotated

from app.config import settings
from app.models.workflow import SalesforceWebhookPayload, WorkflowResponse
from app.services.workflow import WorkflowOrchestrator
from app.utils.logger import setup_logging

# Setup structured logging
setup_logging(settings.log_level)
logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Ada Agent Provisioning Service",
    description="Automated provisioning of Ada AI agents from Salesforce opportunities",
    version="1.0.0"
)

# Initialize workflow orchestrator
workflow = WorkflowOrchestrator()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Ada Agent Provisioning",
        "status": "healthy",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "salesforce": "not_checked",  # Could add actual health checks
            "ada": "not_checked",
            "openai": "not_checked",
            "slack": "not_checked"
        }
    }


@app.post("/webhook/salesforce/opportunity", response_model=WorkflowResponse)
async def handle_salesforce_opportunity(
    payload: SalesforceWebhookPayload,
    background_tasks: BackgroundTasks,
    x_webhook_signature: Annotated[str | None, Header()] = None
):
    """
    Webhook endpoint for Salesforce opportunity stage changes.

    Triggered when an opportunity moves to Stage 0 (Qualified).
    Initiates the Ada agent provisioning workflow in the background.

    Args:
        payload: Salesforce webhook data containing opportunity details
        background_tasks: FastAPI background tasks for async processing
        x_webhook_signature: Optional webhook signature for security validation

    Returns:
        Immediate acknowledgment with workflow_id for tracking
    """
    logger.info(
        "salesforce_webhook_received",
        opportunity_id=payload.opportunity_id,
        stage=payload.stage
    )

    # Validate webhook signature if configured
    if settings.webhook_secret and x_webhook_signature:
        # TODO: Implement signature validation
        # if not validate_signature(payload, x_webhook_signature):
        #     raise HTTPException(status_code=401, detail="Invalid webhook signature")
        pass

    # Validate stage is "Stage 0" (or whatever the actual value is)
    # This will be updated once we know the exact Salesforce stage name
    if payload.stage != "Stage 0":
        logger.warning(
            "invalid_stage",
            opportunity_id=payload.opportunity_id,
            stage=payload.stage,
            expected="Stage 0"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage: {payload.stage}. Expected 'Stage 0'"
        )

    # Generate workflow ID for tracking
    workflow_id = f"wf_{payload.opportunity_id}_{int(payload.timestamp.timestamp())}"

    # Add workflow to background tasks
    background_tasks.add_task(
        workflow.execute,
        opportunity_id=payload.opportunity_id,
        workflow_id=workflow_id
    )

    logger.info(
        "workflow_queued",
        workflow_id=workflow_id,
        opportunity_id=payload.opportunity_id
    )

    return WorkflowResponse(
        success=True,
        workflow_id=workflow_id,
        message=f"Ada agent provisioning workflow started for opportunity {payload.opportunity_id}"
    )


@app.get("/workflow/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get the status of a provisioning workflow.

    Args:
        workflow_id: The workflow identifier returned from the webhook

    Returns:
        Current workflow status and progress
    """
    # TODO: Implement workflow status tracking
    # This would query a database or cache for workflow state
    return {
        "workflow_id": workflow_id,
        "status": "in_progress",
        "message": "Status tracking not yet implemented"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
