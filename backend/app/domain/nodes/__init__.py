"""Node type registration."""

from app.domain.models import NodeType
from app.domain.nodes.base import NodeRegistry
from app.domain.nodes.if_node import IfNode
from app.domain.nodes.llm import LLMNode
from app.domain.nodes.output import OutputNode
from app.domain.nodes.prompt import PromptNode
from app.domain.nodes.setvar import SetVarNode

# Register all node types
NodeRegistry.register(NodeType.PROMPT.value, PromptNode)
NodeRegistry.register(NodeType.LLM.value, LLMNode)
NodeRegistry.register(NodeType.IF.value, IfNode)
NodeRegistry.register(NodeType.SET_VAR.value, SetVarNode)
NodeRegistry.register(NodeType.OUTPUT.value, OutputNode)
