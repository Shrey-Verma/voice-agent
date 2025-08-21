"""Repository for workflow persistence."""

from datetime import datetime
from typing import List, Optional

from app.domain.models import Workflow
from app.infra.supabase_client import SupabaseClient


class WorkflowRepository:
    """Repository for workflow CRUD operations."""

    def __init__(self) -> None:
        """Initialize with Supabase client."""
        self.client = SupabaseClient.get_client()

    async def create(self, workflow: Workflow) -> Workflow:
        """Create a new workflow."""
        try:
            data = {
                "id": workflow.id,
                "name": workflow.name,
                "version": workflow.version,
                "json": workflow.model_dump(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            print(f"Creating workflow with data: {data}")
            
            result = self.client.table("workflows").insert(data).execute()
            print(f"Supabase result: {result}")
            
            # Verify the workflow was saved
            verify = self.client.table("workflows").select("*").eq("id", workflow.id).execute()
            if not verify.data:
                raise Exception(f"Failed to verify workflow creation: {workflow.id}")
                
            return workflow
        except Exception as e:
            print(f"Error in repository create: {str(e)}")
            raise

    async def get(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        result = self.client.table("workflows") \
            .select("*") \
            .eq("id", workflow_id) \
            .execute()
            
        if not result.data:
            return None
            
        return Workflow(**result.data[0]["json"])

    async def update(self, workflow: Workflow) -> Workflow:
        """Update an existing workflow."""
        data = {
            "name": workflow.name,
            "version": workflow.version,
            "json": workflow.model_dump(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = self.client.table("workflows") \
            .update(data) \
            .eq("id", workflow.id) \
            .execute()
            
        return workflow

    async def list(self) -> list[Workflow]:
        """List all workflows."""
        result = self.client.table("workflows") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
            
        return [Workflow(**row["json"]) for row in result.data]

    async def delete(self, workflow_id: str) -> None:
        """Delete a workflow and all associated data."""
        try:
            # First delete run steps
            run_result = self.client.table("runs") \
                .select("id") \
                .eq("workflow_id", workflow_id) \
                .execute()
            
            if run_result.data:
                run_ids = [run["id"] for run in run_result.data]
                # Delete run steps for these runs
                self.client.table("run_steps") \
                    .delete() \
                    .in_("run_id", run_ids) \
                    .execute()
                
                # Delete audit logs for these runs
                self.client.table("audit_logs") \
                    .delete() \
                    .in_("run_id", run_ids) \
                    .execute()
            
            # Delete runs
            self.client.table("runs") \
                .delete() \
                .eq("workflow_id", workflow_id) \
                .execute()
            
            # Finally delete the workflow
            self.client.table("workflows") \
                .delete() \
                .eq("id", workflow_id) \
                .execute()
                
        except Exception as e:
            print(f"Error deleting workflow: {str(e)}")
            raise
