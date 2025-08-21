"""Repository for workflow run persistence."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.models import Run, RunStatus
from app.infra.supabase_client import SupabaseClient


class RunRepository:
    """Repository for run CRUD operations."""

    def __init__(self) -> None:
        """Initialize with Supabase client."""
        self.client = SupabaseClient.get_client()

    async def create(self, run: Run) -> Run:
        """Create a new run record."""
        data = {
            "id": str(run.id),
            "workflow_id": run.workflow_id,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "variables": run.variables
        }
        
        result = self.client.table("runs").insert(data).execute()
        return run

    async def get(self, run_id: UUID) -> Optional[Run]:
        """Get a run by ID."""
        result = self.client.table("runs") \
            .select("*") \
            .eq("id", str(run_id)) \
            .execute()
            
        if not result.data:
            return None
            
        row = result.data[0]
        return Run(
            id=UUID(row["id"]),
            workflow_id=row["workflow_id"],
            status=RunStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=(
                datetime.fromisoformat(row["finished_at"])
                if row["finished_at"]
                else None
            ),
            variables=row["variables"]
        )

    async def update(self, run: Run) -> Run:
        """Update an existing run."""
        data = {
            "status": run.status,
            "finished_at": (
                run.finished_at.isoformat()
                if run.finished_at
                else None
            ),
            "variables": run.variables
        }
        
        result = self.client.table("runs") \
            .update(data) \
            .eq("id", str(run.id)) \
            .execute()
            
        return run
