#!/usr/bin/env python3
"""
FastAPI server for Ada Agent Provisioning
Handles both Zapier webhooks and Web UI requests
"""

import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
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

        # Update job with result - ensure all values are JSON serializable
        jobs[job_id]["status"] = "completed" if result["success"] else "failed"
        # Sanitize result to ensure JSON serialization works
        try:
            # Test JSON serialization
            json.dumps(result)
            jobs[job_id]["result"] = result
        except (TypeError, ValueError) as json_err:
            # If result can't be serialized, store a simplified version
            jobs[job_id]["result"] = {
                "success": result.get("success", False),
                "error": str(result.get("error", "")) if result.get("error") else None,
                "serialization_warning": f"Original result could not be serialized: {str(json_err)}"
            }
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        if result["success"]:
            # Mark all phases as completed
            jobs[job_id]["completed_phases"] = [1, 2, 3, 4, 5, 6, 7]
            jobs[job_id]["current_phase"] = 7
            jobs[job_id]["progress"] = "Provisioning completed successfully!"
        else:
            # Sanitize error message from result
            error_msg = str(result.get("error", "Unknown error"))
            error_msg = error_msg.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            error_msg = error_msg.replace('"', "'").replace('`', "'")
            error_msg = error_msg.replace('\\', '/')
            if len(error_msg) > 300:
                error_msg = error_msg[:300] + "... (truncated)"
            jobs[job_id]["error"] = error_msg

    except Exception as e:
        # Sanitize error message to ensure JSON serialization
        # Get just the exception type and message, not the full repr
        error_msg = f"{type(e).__name__}: {str(e)}"
        # Remove any problematic characters that might break JSON
        error_msg = error_msg.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Replace all quotes with single quotes to avoid escaping issues
        error_msg = error_msg.replace('"', "'").replace('`', "'")
        # Remove backslashes that might cause issues
        error_msg = error_msg.replace('\\', '/')
        # Limit length to avoid huge error messages
        if len(error_msg) > 300:
            error_msg = error_msg[:300] + "... (truncated)"

        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_msg
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    web_dir = Path(__file__).parent / "web"
    index_file = web_dir / "index.html"
    if index_file.exists():
        return index_file.read_text()
    else:
        return {
            "service": "Ada Agent Provisioning API",
            "status": "healthy",
            "version": "1.0.0"
        }

@app.get("/health")
async def health():
    """Health check endpoint for Fly.io."""
    return {"status": "ok"}

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

    job_data = jobs[job_id]

    # Log the raw job data structure for debugging
    print(f"\n{'='*80}")
    print(f"DEBUG: Fetching job {job_id}")
    print(f"Job keys: {list(job_data.keys())}")
    print(f"Status: {job_data.get('status')}")
    print(f"Error field type: {type(job_data.get('error'))}")
    print(f"Error field value (first 200 chars): {str(job_data.get('error'))[:200] if job_data.get('error') else 'None'}")
    print(f"Result field type: {type(job_data.get('result'))}")

    # Try to identify which field is causing the issue
    for key, value in job_data.items():
        try:
            json.dumps({key: value})
            print(f"✓ Field '{key}' serializes OK")
        except Exception as field_err:
            print(f"✗ Field '{key}' FAILS serialization: {type(field_err).__name__}: {str(field_err)[:100]}")
    print(f"{'='*80}\n")

    # Ensure the job data is JSON serializable before returning
    try:
        # Test full serialization
        serialized = json.dumps(job_data)
        print(f"DEBUG: Full serialization successful, length: {len(serialized)}")
        return job_data
    except (TypeError, ValueError) as e:
        # Log the exact error with more detail
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"DEBUG: Serialization failed - {error_type}: {error_msg[:500]}")

        # If serialization fails, return a sanitized version
        return {
            "job_id": job_data.get("job_id", job_id),
            "status": job_data.get("status", "unknown"),
            "created_at": job_data.get("created_at", ""),
            "updated_at": job_data.get("updated_at", ""),
            "company_name": job_data.get("company_name", ""),
            "progress": job_data.get("progress"),
            "current_phase": job_data.get("current_phase"),
            "completed_phases": job_data.get("completed_phases", []),
            "result": None,
            "error": f"Serialization error: {error_type}"
        }

@app.get("/api/jobs/{job_id}/debug")
async def get_job_debug(job_id: str):
    """Debug endpoint - returns job data as plain text to avoid JSON issues."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = jobs[job_id]

    # Return as plain text representation
    from fastapi.responses import PlainTextResponse
    import pprint

    debug_output = f"""
JOB DEBUG OUTPUT
================
Job ID: {job_id}

RAW DATA STRUCTURE:
{pprint.pformat(job_data, width=120)}

FIELD ANALYSIS:
"""
    for key, value in job_data.items():
        debug_output += f"\n{key}:"
        debug_output += f"\n  Type: {type(value)}"
        debug_output += f"\n  Repr: {repr(value)[:500]}"
        try:
            json.dumps({key: value})
            debug_output += f"\n  JSON: ✓ Serializable"
        except Exception as e:
            debug_output += f"\n  JSON: ✗ {type(e).__name__}: {str(e)[:200]}"

    return PlainTextResponse(debug_output)

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
    port = int(os.getenv("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)
