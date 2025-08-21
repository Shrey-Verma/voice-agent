"""Service layer for workflow operations."""

from typing import List, Optional

from app.domain.models import Workflow
from app.infra.repositories.workflows_repo import WorkflowRepository


class WorkflowService:
    """Service for workflow operations."""

    def __init__(self) -> None:
        """Initialize with repository."""
        self.repo = WorkflowRepository()

    async def create_workflow(self, workflow: Workflow) -> Workflow:
        """Create a new workflow.
        
        Validates the workflow structure and persists it.
        """
        try:
            # Basic validation is handled by Pydantic model
            
            # Additional validation could be added here:
            # - Check for cycles in graph
            # - Validate node references
            # - etc.
            
            return await self.repo.create(workflow)
        except Exception as e:
            print(f"Error creating workflow: {str(e)}")
            raise

    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return await self.repo.get(workflow_id)

    async def update_workflow(self, workflow: Workflow) -> Workflow:
        """Update an existing workflow."""
        # Ensure workflow exists
        existing = await self.repo.get(workflow.id)
        if not existing:
            raise ValueError(f"Workflow {workflow.id} not found")
            
        # Increment version
        workflow.version = existing.version + 1
        
        return await self.repo.update(workflow)

    async def list_workflows(self) -> List[Workflow]:
        """List all workflows."""
        return await self.repo.list()

    async def delete_workflow(self, workflow_id: str) -> None:
        """Delete a workflow."""
        # Ensure workflow exists
        existing = await self.repo.get(workflow_id)
        if not existing:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        await self.repo.delete(workflow_id)
