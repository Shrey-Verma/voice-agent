"""Core domain models for the workflow engine."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    """Available node types in the workflow."""
    PROMPT = "Prompt"
    LLM = "LLM"
    IF = "If"
    SET_VAR = "SetVar"
    OUTPUT = "Output"


class Node(BaseModel):
    """Base node model."""
    id: str
    type: NodeType
    config: Dict[str, Any] = Field(default_factory=dict)
    next: Optional[str] = None


class Edge(BaseModel):
    """Edge connecting two nodes with optional condition."""
    id: str
    source: str
    target: str
    condition: Optional[str] = None


class Workflow(BaseModel):
    """Complete workflow definition."""
    id: str
    name: str
    version: int = 1
    variables: Dict[str, Any] = Field(default_factory=dict)
    nodes: List[Node]
    edges: Optional[List[Edge]] = None

    @field_validator("nodes")
    def validate_nodes(cls, v: List[Node]) -> List[Node]:
        """Ensure at least one node exists."""
        if not v:
            raise ValueError("Workflow must have at least one node")
        return v


class RunStatus(str, Enum):
    """Possible states of a workflow run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Message(BaseModel):
    """A message in the conversation."""
    role: str
    content: str
    name: Optional[str] = None


class ConversationState(BaseModel):
    """Current state of a workflow run."""
    messages: List[Message] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    last_node: Optional[str] = None
    done: bool = False


class RunStep(BaseModel):
    """Record of a single node execution."""
    id: UUID
    run_id: UUID
    node_id: str
    input_messages: List[Message] = Field(default_factory=list)
    output_messages: List[Message] = Field(default_factory=list)
    variables_snapshot: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: Optional[int] = None
    created_at: datetime


class Run(BaseModel):
    """Complete workflow run record."""
    id: UUID
    workflow_id: str
    status: RunStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    steps: List[RunStep] = Field(default_factory=list)


class NodeIO(BaseModel):
    """Input/output specification for a node."""
    inputs: Dict[str, str] = Field(default_factory=dict)
    outputs: Dict[str, str] = Field(default_factory=dict)
    description: str
