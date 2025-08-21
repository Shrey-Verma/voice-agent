"""Service layer for workflow run operations."""

from datetime import datetime
from time import time
from uuid import UUID, uuid4

from app.core.engine import WorkflowEngine
from app.domain.models import ConversationState, Run, RunStatus, RunStep
from app.infra.repositories.run_steps_repo import RunStepsRepository
from app.infra.repositories.runs_repo import RunRepository
from app.services.workflow_service import WorkflowService


class RunService:
    """Service for workflow run operations."""

    def __init__(self) -> None:
        """Initialize with repositories."""
        self.runs_repo = RunRepository()
        self.steps_repo = RunStepsRepository()
        self.workflow_service = WorkflowService()

    async def start_run(
        self,
        workflow_id: str,
        input_text: str | None = None
    ) -> Run:
        """Start a new workflow run."""
        # Get workflow
        workflow = await self.workflow_service.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create run record
        run_id = uuid4()
        run = Run(
            id=run_id,
            workflow_id=workflow_id,
            status=RunStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        # Initialize engine
        engine = WorkflowEngine(workflow)
        
        # Start workflow
        state = engine.start(input_text)
        
        # Update run with state
        run.variables = state.variables
        
        # Save run
        await self.runs_repo.create(run)
        
        return run

    async def step_run(self, run_id: UUID, user_text: str) -> Run:
        """Process a user message in a run."""
        # Get run
        run = await self.runs_repo.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        # Check status
        if run.status != RunStatus.RUNNING:
            raise ValueError(f"Run {run_id} is not running")
        
        # Get workflow
        workflow = await self.workflow_service.get_workflow(run.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {run.workflow_id} not found")
        
        # Initialize engine
        engine = WorkflowEngine(workflow)
        
        # Load previous steps
        steps = await self.steps_repo.get_by_run(run.id)
        
        # Create state from run and steps
        messages = []
        for step in steps:
            # Add input messages first
            messages.extend(step.input_messages)
            # Then add output messages
            messages.extend(step.output_messages)
        
        state = ConversationState(
            variables=run.variables,
            messages=messages,
            last_node=steps[-1].node_id if steps else None,
            done=False
        )
        
        # Record start time
        start_time = time()
        
        # Process message
        state = engine.step(state, user_text)
        
        # Calculate latency
        latency_ms = int((time() - start_time) * 1000)
        
        # Create step record
        step = RunStep(
            id=uuid4(),
            run_id=run.id,
            node_id=state.last_node or "unknown",
            # User message and prompt
            input_messages=state.messages[-2:] if len(state.messages) > 1 else state.messages,
            output_messages=state.messages[-1:] if state.messages else [],  # LLM response
            variables_snapshot=state.variables,
            latency_ms=latency_ms,
            created_at=datetime.utcnow()
        )
        
        # Save step
        await self.steps_repo.create(step)
        
        # Update run
        run.variables = state.variables
        
        # Save run
        await self.runs_repo.update(run)
        
        return run

    async def get_run(self, run_id: UUID) -> Run | None:
        """Get a run by ID."""
        return await self.runs_repo.get(run_id)

    async def get_run_steps(self, run_id: UUID) -> list[RunStep]:
        """Get all steps for a run."""
        return await self.steps_repo.get_by_run(run_id)
