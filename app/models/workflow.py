"""Pydantic models for workflow data structures."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class SalesforceWebhookPayload(BaseModel):
    """
    Payload received from Salesforce webhook when opportunity stage changes.

    This will be updated once we see the actual webhook payload structure.
    """
    opportunity_id: str = Field(..., description="Salesforce Opportunity ID")
    stage: str = Field(..., description="Opportunity stage name")
    account_id: str | None = Field(None, description="Salesforce Account ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")

    # Additional fields that might be in the payload
    owner_id: str | None = None
    opportunity_name: str | None = None
    amount: float | None = None


class WorkflowResponse(BaseModel):
    """Response returned immediately to webhook caller."""
    success: bool
    workflow_id: str
    message: str


class WorkflowStatus(BaseModel):
    """Status of a running or completed workflow."""
    workflow_id: str
    status: Literal["queued", "in_progress", "completed", "failed"]
    opportunity_id: str
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    steps_completed: list[str] = Field(default_factory=list)
    current_step: str | None = None


class WorkflowContext(BaseModel):
    """
    Context data passed through the workflow.

    This accumulates data from each step to be used by subsequent steps.
    """
    # Identifiers
    workflow_id: str
    opportunity_id: str

    # Salesforce data
    account_id: str | None = None
    account_name: str | None = None
    partner_name: str | None = None
    consultant_info: dict | None = None
    is_new_customer: bool = False

    # Generated content
    company_description: str | None = None
    knowledge_articles: list[dict] | None = None
    tk_questions: list[str] | None = None
    endpoints: list[dict] | None = None

    # Ada resources created
    knowledge_source_id: str | None = None
    endpoint_ids: list[str] = Field(default_factory=list)
    channel_id: str | None = None
    conversation_ids: list[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
