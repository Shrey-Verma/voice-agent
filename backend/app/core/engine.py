"""Core workflow engine that builds and runs LangGraph workflows."""

import inspect
from typing import Annotated, Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

from app.core.router import create_router
from app.domain.models import ConversationState, Message, Node, Workflow
from app.domain.nodes.base import NodeRegistry

# Constants
CONFIG_PARAM_COUNT = 2


def _convert_to_langchain_message(msg: Message) -> AIMessage | HumanMessage | SystemMessage:
    """Convert our Message to LangChain message type."""
    # Convert content to string if it's not already
    content = str(msg.content) if not isinstance(msg.content, str) else msg.content
    
    if msg.role == "assistant":
        return AIMessage(content=content)
    elif msg.role == "user":
        return HumanMessage(content=content)
    elif msg.role == "system":
        return SystemMessage(content=content)
    else:
        raise ValueError(f"Unknown message role: {msg.role}")


def _convert_from_langchain_message(msg: AIMessage | HumanMessage | SystemMessage) -> Message:
    """Convert LangChain message to our Message type."""
    # Convert content to string if it's not already
    content = str(msg.content) if not isinstance(msg.content, str) else msg.content
    
    if isinstance(msg, AIMessage):
        role = "assistant"
    elif isinstance(msg, HumanMessage):
        role = "user"
    elif isinstance(msg, SystemMessage):
        role = "system"
    else:
        raise ValueError(f"Unknown message type: {type(msg)}")
    
    return Message(role=role, content=content)


class State(TypedDict):
    """Graph state with message history."""
    messages: Annotated[list, add_messages]
    variables: dict
    last_node: str | None
    done: bool


class WorkflowEngine:
    """Builds and runs LangGraph workflows."""

    def __init__(self, workflow: Workflow) -> None:
        """Initialize with a workflow definition."""
        self.workflow = workflow
        self.compiled_graph: CompiledStateGraph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        """Convert workflow definition to LangGraph StateGraph and compile it."""
        # Create graph with State
        graph = StateGraph(State)
        
        # Add all nodes
        for node in self.workflow.nodes:
            # Create node instance
            node_instance = NodeRegistry.create(node)
            # Get graph function
            fn = node_instance.to_graph_fn()
            
            # Create a wrapper function that matches LangGraph's expected signature
            # Node functions can accept (state) or (state, config)
            def create_node_fn(node_func, node_id):
                # Check if the function accepts config parameter
                sig = inspect.signature(node_func)
                params = list(sig.parameters.keys())
                
                def wrapper(state: State) -> dict[str, Any]:
                    # Convert messages to our type
                    messages = [
                        _convert_from_langchain_message(msg) 
                        for msg in state.get("messages", [])
                    ]
                    
                    # Convert dict state to ConversationState
                    conv_state = ConversationState(
                        messages=messages,
                        variables=state.get("variables", {}),
                        last_node=state.get("last_node"),
                        done=state.get("done", False)
                    )
                    
                    # Call node function based on signature
                    if len(params) >= CONFIG_PARAM_COUNT:
                        result = node_func(conv_state, {})
                    else:
                        result = node_func(conv_state)
                    
                    # Get new messages (only the ones added by this node)
                    new_messages = []
                    if result:
                        start_idx = len(messages)
                        new_messages = result.messages[start_idx:]
                    
                    # Convert result back to dict with LangChain messages
                    return {
                        "messages": [
                            *state.get("messages", []),  # Keep existing messages
                            # Add new messages
                            *[_convert_to_langchain_message(msg) for msg in new_messages]
                        ],
                        "last_node": node_id,
                        "variables": result.variables if result else state.get("variables", {}),
                        "done": result.done if result else False
                    }
                return wrapper
            
            # Create the wrapped function with proper node_id
            wrapped_fn = create_node_fn(fn, node.id)
            
            # Add to graph - pass node name and function separately
            graph.add_node(node.id, wrapped_fn)
        
        # Set entry point - connect START to first node
        if self.workflow.nodes:
            graph.add_edge(START, self.workflow.nodes[0].id)
            # When starting, only run the first node
            graph.add_edge(self.workflow.nodes[0].id, END)
        
        # Add edges based on workflow definition
        if self.workflow.edges:
            # Use explicit edges
            for edge in self.workflow.edges:
                if edge.condition:
                    # Create router function for conditional edges
                    def create_route_condition(edge_obj):
                        def route_condition(state: State) -> str:
                            router = create_router(edge_obj.condition)
                            # Convert State to ConversationState for router
                            conv_state = self._state_to_conversation(state)
                            return edge_obj.target if router(conv_state) else END
                        return route_condition
                    
                    # Add conditional edges
                    graph.add_conditional_edges(
                        edge.source,
                        create_route_condition(edge),
                        {edge.target: edge.target, END: END}
                    )
                else:
                    # Add direct edge
                    graph.add_edge(edge.source, edge.target)
        else:
            # Use next pointers from nodes
            for node in self.workflow.nodes:
                if node.next:
                    graph.add_edge(node.id, node.next)
                elif node == self.workflow.nodes[-1]:
                    # Connect last node to END if no next is specified
                    graph.add_edge(node.id, END)
        
        # Compile the graph and return CompiledStateGraph
        return graph.compile()

    def _state_to_conversation(self, state: dict[str, Any] | State) -> ConversationState:
        """Convert graph state to ConversationState."""
        # Convert LangChain messages to our Message type
        messages = [
            _convert_from_langchain_message(msg)
            for msg in state.get("messages", [])
        ]
        
        return ConversationState(
            messages=messages,
            variables=state.get("variables", {}),
            last_node=state.get("last_node"),
            done=state.get("done", False)
        )

    def _conversation_to_state(self, conv_state: ConversationState) -> State:
        """Convert ConversationState to graph state."""
        # Convert our Message type to LangChain messages
        messages = [
            _convert_to_langchain_message(msg)
            for msg in conv_state.messages
        ]
        
        return State(
            messages=messages,
            variables=conv_state.variables,
            last_node=conv_state.last_node,
            done=conv_state.done
        )

    def start(self, input_text: str | None = None) -> ConversationState:
        """Start a new workflow run."""
        if not self.workflow.nodes:
            return ConversationState()
        
        # Create initial state
        initial_state: State = {
            "messages": [],
            "variables": self.workflow.variables.copy(),
            "last_node": None,
            "done": False
        }
        
        # Add input message if provided
        if input_text:
            initial_state["messages"].append(
                HumanMessage(content=input_text)
            )
        
        # Run first node (Prompt) to get initial message
        first_node = self.workflow.nodes[0]
        node_instance = NodeRegistry.create(first_node)
        fn = node_instance.to_graph_fn()
        
        # Convert state and run function
        conv_state = self._state_to_conversation(initial_state)
        result = fn(conv_state)
        
        # Update state
        result.last_node = first_node.id
        result.done = False
        
        # If we have input text, run the next node (LLM) immediately
        if input_text and not result.done:
            # Find next node
            next_node = None
            if self.workflow.edges:
                for edge in self.workflow.edges:
                    if edge.source == first_node.id:
                        next_node = self._find_node_by_id(edge.target)
                        break
            if not next_node and first_node.next:
                next_node = self._find_node_by_id(first_node.next)
            
            if next_node and next_node.type == "LLM":
                # Add user message to state
                result.messages.append(Message(role="user", content=input_text))
                
                # Create node instance and get function
                next_node_instance = NodeRegistry.create(next_node)
                next_fn = next_node_instance.to_graph_fn()
                
                # Run LLM node
                result = next_fn(result)
                
                # Update state
                result.last_node = next_node.id
                result.done = not self._has_next_node(next_node)
                
                # If we have an output node next, run it too
                if not result.done:
                    next_next_node = None
                    if self.workflow.edges:
                        for edge in self.workflow.edges:
                            if edge.source == next_node.id:
                                next_next_node = self._find_node_by_id(edge.target)
                                break
                    if not next_next_node and next_node.next:
                        next_next_node = self._find_node_by_id(next_node.next)
                    
                    if next_next_node and next_next_node.type == "Output":
                        # Create node instance and get function
                        next_next_node_instance = NodeRegistry.create(next_next_node)
                        next_next_fn = next_next_node_instance.to_graph_fn()
                        
                        # Run output node
                        result = next_next_fn(result)
                        
                        # Update state
                        result.last_node = next_next_node.id
                        result.done = not self._has_next_node(next_next_node)
        
        return result

    def _find_node_by_id(self, node_id: str) -> Node | None:
        """Find a node by its ID."""
        for node in self.workflow.nodes:
            if node.id == node_id:
                return node
        return None

    def _find_next_node_from_edges(self, current_node_id: str) -> Node | None:
        """Find next node using workflow edges."""
        if not self.workflow.edges:
            return None
            
        for edge in self.workflow.edges:
            if edge.source == current_node_id:
                return self._find_node_by_id(edge.target)
        return None

    def _find_next_node_from_next_prop(self, current_node_id: str) -> Node | None:
        """Find next node using node's next property."""
        current_node = self._find_node_by_id(current_node_id)
        if current_node and current_node.next:
            return self._find_node_by_id(current_node.next)
        return None

    def _has_next_node(self, node: Node) -> bool:
        """Check if a node has a next node."""
        if self.workflow.edges:
            return any(edge.source == node.id for edge in self.workflow.edges)
        return bool(node.next)

    def step(self, state: ConversationState, user_text: str) -> ConversationState:
        """Process a user message and advance the workflow."""
        if not self.workflow.nodes:
            return state
        
        # Find next node
        next_node = None
        if not state.last_node:
            # Start from first node
            next_node = self.workflow.nodes[0]
        else:
            # Try finding next node from edges first
            next_node = self._find_next_node_from_edges(state.last_node)
            if not next_node:
                # Fall back to next property
                next_node = self._find_next_node_from_next_prop(state.last_node)
        
        if not next_node:
            # No next node found, workflow is done
            state.done = True
            return state
        
        # Create node instance and get function
        node_instance = NodeRegistry.create(next_node)
        fn = node_instance.to_graph_fn()
        
        # Add user message to state
        state.messages.append(Message(role="user", content=user_text))
        
        # Run node function
        result = fn(state)
        
        # Update state
        result.last_node = next_node.id
        result.done = not self._has_next_node(next_node)
        
        # If this was a Prompt node, we need to run the next node (LLM) immediately
        if next_node.type == "Prompt":
            # Find next node
            next_next_node = self._find_next_node_from_edges(next_node.id)
            if not next_next_node:
                next_next_node = self._find_next_node_from_next_prop(next_node.id)
            
            if next_next_node and next_next_node.type == "LLM":
                # Create node instance and get function
                next_node_instance = NodeRegistry.create(next_next_node)
                next_fn = next_node_instance.to_graph_fn()
                
                # Run LLM node with the same state
                result = next_fn(result)
                
                # Update state
                result.last_node = next_next_node.id
                result.done = not self._has_next_node(next_next_node)
                
                # If we have an output node next, run it too
                if not result.done:
                    next_next_next_node = self._find_next_node_from_edges(next_next_node.id)
                    if not next_next_next_node:
                        next_next_next_node = self._find_next_node_from_next_prop(next_next_node.id)
                    
                    if next_next_next_node and next_next_next_node.type == "Output":
                        # Create node instance and get function
                        next_next_node_instance = NodeRegistry.create(next_next_next_node)
                        next_next_fn = next_next_node_instance.to_graph_fn()
                        
                        # Run output node
                        result = next_next_fn(result)
                        
                        # Update state
                        result.last_node = next_next_next_node.id
                        result.done = not self._has_next_node(next_next_next_node)
        # If this was an LLM node, we need to run the next node (Output) immediately
        elif next_node.type == "LLM" and not result.done:
            # Find next node
            next_next_node = self._find_next_node_from_edges(next_node.id)
            if not next_next_node:
                next_next_node = self._find_next_node_from_next_prop(next_node.id)
            
            if next_next_node and next_next_node.type == "Output":
                # Create node instance and get function
                next_node_instance = NodeRegistry.create(next_next_node)
                next_fn = next_node_instance.to_graph_fn()
                
                # Run output node
                result = next_fn(result)
                
                # Update state
                result.last_node = next_next_node.id
                result.done = not self._has_next_node(next_next_node)
        
        return result
    
    def stream(self, state: ConversationState, user_text: str | None = None):
        """Stream workflow execution for real-time updates."""
        # Convert ConversationState to graph state
        graph_state = self._conversation_to_state(state)
        
        # Add user message if provided
        if user_text:
            graph_state["messages"].append(
                Message(role="user", content=user_text)
            )
        
        # Stream results
        for chunk in self.compiled_graph.stream(graph_state):
            yield self._state_to_conversation(chunk)
    
    async def astep(self, state: ConversationState, user_text: str) -> ConversationState:
        """Async version of step method."""
        # Convert ConversationState to graph state
        graph_state = self._conversation_to_state(state)
        
        # Add user message
        graph_state["messages"].append(
            HumanMessage(content=user_text)
        )
        
        # Run compiled graph using ainvoke
        result = await self.compiled_graph.ainvoke(graph_state)
        
        # Convert result back to ConversationState
        return self._state_to_conversation(result)