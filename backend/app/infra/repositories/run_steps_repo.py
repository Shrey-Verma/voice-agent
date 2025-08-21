"""Repository for workflow run steps persistence."""

from datetime import datetime
from uuid import UUID

from app.domain.models import Message, RunStep
from app.infra.supabase_client import SupabaseClient


class RunStepsRepository:
    """Repository for run steps CRUD operations."""

    def __init__(self) -> None:
        """Initialize with Supabase client."""
        self.client = SupabaseClient.get_client()

    async def create(self, step: RunStep) -> RunStep:
        """Create a new run step record."""
        data = {
            "id": str(step.id),
            "run_id": str(step.run_id),
            "node_id": step.node_id,
            "input": {
                "messages": [msg.model_dump() for msg in step.input_messages]
            },
            "output": {
                "messages": [msg.model_dump() for msg in step.output_messages]
            },
            "variables_snapshot": step.variables_snapshot,
            "latency_ms": step.latency_ms,
            "created_at": step.created_at.isoformat()
        }
        
        self.client.table("run_steps").insert(data).execute()
        return step

    async def get_by_run(self, run_id: UUID) -> list[RunStep]:
        """Get all steps for a run."""
        result = self.client.table("run_steps") \
            .select("*") \
            .eq("run_id", str(run_id)) \
            .order("created_at", desc=False) \
            .execute()
            
        if not result.data:
            return []
            
        steps = []
        for row in result.data:
            # Convert messages from JSON
            input_messages = [
                Message(**msg)
                for msg in row["input"].get("messages", [])
            ]
            output_messages = [
                Message(**msg)
                for msg in row["output"].get("messages", [])
            ]
            
            step = RunStep(
                id=UUID(row["id"]),
                run_id=UUID(row["run_id"]),
                node_id=row["node_id"],
                input_messages=input_messages,
                output_messages=output_messages,
                variables_snapshot=row["variables_snapshot"],
                latency_ms=row["latency_ms"],
                created_at=datetime.fromisoformat(row["created_at"])
            )
            steps.append(step)
            
        return steps
