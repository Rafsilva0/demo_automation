#!/usr/bin/env python3
"""
FastAPI server for Ada Agent Provisioning
Handles both Zapier webhooks and Web UI requests
"""

import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import json
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️ No .env file found at {env_path}")

# Import our provisioning module
from provision import provision_demo

app = FastAPI(
    title="Ada Agent Provisioning API",
    description="API for automated Ada agent demo provisioning",
    version="1.0.0"
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job tracking (use Redis/DB in production)
jobs: Dict[str, Dict[str, Any]] = {}

class ProvisionRequest(BaseModel):
    """Request model for manual provisioning via web UI."""
    company_name: str = Field(..., description="Company name", min_length=1)
    ada_api_key: Optional[str] = Field(None, description="Ada API key (optional if auto-retrieve enabled)")
    auto_retrieve_key: bool = Field(False, description="Automatically retrieve Ada API key via Playwright")
    company_description: Optional[str] = Field(None, description="Custom company description")
    num_articles: int = Field(10, description="Number of knowledge articles", ge=1, le=50)
    num_questions: int = Field(70, description="Number of customer questions", ge=1, le=200)
    num_conversations: Optional[int] = Field(None, description="Number of conversations to create")

class SalesforceWebhook(BaseModel):
    """Webhook payload from Salesforce/Zapier."""
    opportunity_id: str
    account_name: str
    stage: str
    ada_api_key: Optional[str] = None

class JobResponse(BaseModel):
    """Response model for job submission."""
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    """Model for job status."""
    job_id: str
    status: str
    created_at: str
    updated_at: str
    company_name: str
    progress: Optional[str] = None
    current_phase: Optional[int] = None
    completed_phases: Optional[list] = []
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

async def run_provisioning_job(job_id: str, request: ProvisionRequest):
    """Background task to run provisioning."""
    try:
        # Update job status
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = "Starting provisioning..."
        jobs[job_id]["current_phase"] = 1
        jobs[job_id]["completed_phases"] = []
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        # Progress callback to update job status
        def update_progress(phase: int, message: str):
            """Update job progress with current phase."""
            jobs[job_id]["current_phase"] = phase
            jobs[job_id]["progress"] = message
            jobs[job_id]["updated_at"] = datetime.now().isoformat()

            # Mark previous phases as completed
            completed = []
            for p in range(1, phase):
                if p not in completed:
                    completed.append(p)
            jobs[job_id]["completed_phases"] = completed

        # Run provisioning
        result = await provision_demo(
            company_name=request.company_name,
            ada_api_key=request.ada_api_key,
            auto_retrieve_key=request.auto_retrieve_key,
            company_description=request.company_description,
            num_articles=request.num_articles,
            num_questions=request.num_questions,
            num_conversations=request.num_conversations,
            dry_run=False,
            progress_callback=update_progress
        )

        # Update job with result
        jobs[job_id]["status"] = "completed" if result["success"] else "failed"
        jobs[job_id]["result"] = result
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        if result["success"]:
            # Mark all phases as completed
            jobs[job_id]["completed_phases"] = [1, 2, 3, 4, 5, 6, 7]
            jobs[job_id]["current_phase"] = 7
            jobs[job_id]["progress"] = "Provisioning completed successfully!"
        else:
            jobs[job_id]["error"] = result.get("error", "Unknown error")

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Ada Agent Provisioning API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/api/provision", response_model=JobResponse)
async def provision(request: ProvisionRequest, background_tasks: BackgroundTasks):
    """
    Create a new provisioning job.
    Returns immediately with a job_id for status tracking.
    """
    # Validate request
    if not request.ada_api_key and not request.auto_retrieve_key:
        raise HTTPException(
            status_code=400,
            detail="Must provide either ada_api_key or enable auto_retrieve_key"
        )

    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "company_name": request.company_name,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result": None,
        "error": None
    }

    # Start background task
    background_tasks.add_task(run_provisioning_job, job_id, request)

    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Provisioning job started for {request.company_name}"
    )

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a provisioning job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]

@app.get("/api/jobs", response_model=list[JobStatus])
async def list_jobs(limit: int = 50):
    """List all provisioning jobs."""
    job_list = list(jobs.values())
    # Sort by created_at descending
    job_list.sort(key=lambda x: x["created_at"], reverse=True)
    return job_list[:limit]

@app.post("/api/webhook/salesforce")
async def salesforce_webhook(webhook: SalesforceWebhook, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for Salesforce/Zapier.
    Triggers provisioning when opportunity reaches Stage 0.
    """
    # Validate stage
    if webhook.stage != "Stage 0":
        return {
            "status": "ignored",
            "message": f"Opportunity not in Stage 0 (current: {webhook.stage})"
        }

    # Create provisioning request
    request = ProvisionRequest(
        company_name=webhook.account_name,
        ada_api_key=webhook.ada_api_key,
        auto_retrieve_key=webhook.ada_api_key is None
    )

    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "company_name": webhook.account_name,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
        "source": "salesforce_webhook",
        "opportunity_id": webhook.opportunity_id
    }

    # Start background task
    background_tasks.add_task(run_provisioning_job, job_id, request)

    return {
        "status": "accepted",
        "job_id": job_id,
        "message": f"Provisioning started for {webhook.account_name}"
    }

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job from history."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]
    return {"status": "deleted", "job_id": job_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
