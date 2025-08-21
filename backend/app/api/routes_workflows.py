"""API routes for workflow management."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.domain.models import Workflow
from app.services.workflow_service import WorkflowService

router = APIRouter()
service = WorkflowService()


@router.post("/", response_model=Workflow)
async def create_workflow(workflow: Workflow) -> Workflow:
    """Create a new workflow."""
    try:
        return await service.create_workflow(workflow)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str) -> Workflow:
    """Get a workflow by ID."""
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: str, workflow: Workflow) -> Workflow:
    """Update an existing workflow."""
    if workflow_id != workflow.id:
        raise HTTPException(
            status_code=400,
            detail="Path workflow_id must match workflow.id"
        )
    
    try:
        return await service.update_workflow(workflow)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[Workflow])
async def list_workflows() -> List[Workflow]:
    """List all workflows."""
    return await service.list_workflows()


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str) -> None:
    """Delete a workflow."""
    try:
        await service.delete_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
