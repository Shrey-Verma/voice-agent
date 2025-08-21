"""Seed script to insert example workflow."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app.domain.models import Node, NodeType, Workflow
from app.services.workflow_service import WorkflowService

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")


async def main() -> None:
    """Insert example greeting workflow."""
    # Create example workflow
    workflow = Workflow(
        id="greeting-workflow",
        name="Simple Greeting",
        version=1,
        variables={},
        nodes=[
            Node(
                id="ask_name",
                type=NodeType.PROMPT,
                config={
                    "text": "Hi! What's your name?"
                },
                next="reply"
            ),
            Node(
                id="reply",
                type=NodeType.OUTPUT,
                config={
                    "text": "Thanks, {{name}}!"
                }
            )
        ]
    )
    
    # Save to database
    service = WorkflowService()
    await service.create_workflow(workflow)
    print(f"Created workflow: {workflow.id}")


if __name__ == "__main__":
    asyncio.run(main())
