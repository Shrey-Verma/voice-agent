"""API routes for workflow runs."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domain.models import Run, RunStep
from app.services.run_service import RunService

router = APIRouter()
service = RunService()


class StartRunRequest(BaseModel):
    """Request to start a workflow run."""
    workflow_id: str
    input_text: str | None = None


class StepRunRequest(BaseModel):
    """Request to step a workflow run."""
    user_text: str


@router.post("/", response_model=Run)
async def start_run(request: StartRunRequest) -> Run:
    """Start a new workflow run."""
    try:
        return await service.start_run(
            request.workflow_id,
            request.input_text
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{run_id}/step", response_model=Run)
async def step_run(run_id: UUID, request: StepRunRequest) -> Run:
    """Process a user message in a run."""
    try:
        return await service.step_run(run_id, request.user_text)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{run_id}", response_model=Run)
async def get_run(run_id: UUID) -> Run:
    """Get a run by ID."""
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/steps", response_model=list[RunStep])
async def get_run_steps(run_id: UUID) -> list[RunStep]:
    """Get all steps for a run."""
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    steps = await service.get_run_steps(run_id)
    return steps
